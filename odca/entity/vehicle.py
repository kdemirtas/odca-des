"""Vehicle: base class for all vehicles in ODCA-DES.

Each vehicle is a SimPy process that moves cell-by-cell through the freeway
using the request-wait-seize-delay-release protocol. Two concurrent processes:
  1. Movement process: cell-by-cell resource acquisition
  2. Driver process: periodic speed and direction evaluation

Each vehicle receives its own numpy RNG for behavioral stochasticity,
spawned from the simulation's RNGRegistry for full reproducibility.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional

import numpy as np
import simpy

from odca.infrastructure.cell import Cell
from odca.models.car_following import newell
from odca.models.lane_changing.mandatory import mlc_probability
from odca.models.lane_changing.discretionary import dlc_probability

logger = logging.getLogger(__name__)


class VehicleType(Enum):
    HDV = "hdv"
    AV = "av"


class Direction(Enum):
    FORWARD = "forward"
    LEFT = "left"
    RIGHT = "right"


@dataclass
class TrajectoryRecord:
    """A single passage-time record: T(x, n)."""
    time: float
    cell_idx: int
    lane_idx: int
    speed: float


class Vehicle:
    _id_counter = 0

    def __init__(
        self,
        env: simpy.Environment,
        rng_slowdown: np.random.Generator,
        rng_mlc: np.random.Generator,
        rng_dlc: np.random.Generator,
        vtype: VehicleType,
        # Behavioral parameters (all floats for continuous speed)
        tau: float,
        standstill_spacing: float,
        v_max: float,
        slowdown_prob: float,
        slowdown_delta: float,
        action_interval: float,
        # Lane change parameters
        mlc_k: float,
        mlc_r0: float,
        dlc_k: float,
        dlc_v0: float,
        dlc_cooldown: float,
        safety_gap_front: float,
        safety_gap_rear: float,
        look_ahead: int,
        look_behind: int,
        # Route
        origin_cell: Optional[Cell] = None,
        destination_cell_idx: Optional[int] = None,
        destination_lane: int = 1,  # rightmost lane for off-ramp exits
    ):
        self.id = Vehicle._id_counter
        Vehicle._id_counter += 1
        self.env = env
        # Per-source RNGs: one stream per randomness source, shared across vehicles
        self.rng_slowdown = rng_slowdown
        self.rng_mlc = rng_mlc
        self.rng_dlc = rng_dlc
        self.vtype = vtype

        # Behavioral parameters
        self.tau = tau
        self.d = standstill_spacing
        self.v_max = v_max
        self.slowdown_prob = slowdown_prob
        self.slowdown_delta = slowdown_delta
        self.action_interval = action_interval

        # Lane change
        self.mlc_k = mlc_k
        self.mlc_r0 = mlc_r0
        self.dlc_k = dlc_k
        self.dlc_v0 = dlc_v0
        self.dlc_cooldown = dlc_cooldown
        self.safety_gap_front = safety_gap_front
        self.safety_gap_rear = safety_gap_rear
        self.look_ahead = look_ahead
        self.look_behind = look_behind

        # Route
        self.origin_cell = origin_cell
        self.destination_cell_idx = destination_cell_idx
        self.destination_lane = destination_lane
        self.initial_distance: Optional[float] = None

        # State
        self.cell: Optional[Cell] = None
        self._cell_entry_time: float = 0.0  # when current cell was entered
        self.speed: float = 0.0
        self.desired_speed: float = v_max
        self.desired_direction: Direction = Direction.FORWARD
        self.active: bool = False
        self.last_lc_time: float = -999.0
        self._driver_proc: Optional[simpy.Process] = None
        self._wake_event: Optional[simpy.Event] = None
        self._last_eval_time: float = -999.0

        # Trajectory log: the T(x, n) output
        self.trajectory: List[TrajectoryRecord] = []

        # Entry/exit times
        self.time_entered: Optional[float] = None
        self.time_exited: Optional[float] = None

        # Blockage waiting tracker: timestamp when vehicle first detected
        # a blockage ahead.  Used to escalate lateral-move priority so that
        # vehicles stuck longer get to merge first.
        self._blockage_wait_since: Optional[float] = None

        # Event counters
        self.count_lane_changes: int = 0
        self.count_lc_failures: int = 0
        self.count_slowdowns: int = 0
        self.count_cf_evaluations: int = 0

    # ------------------------------------------------------------------
    # Resource protocol
    # ------------------------------------------------------------------

    def _request(self, cell: Cell, priority: float = 0.0):
        """Create a PriorityResource request for a cell."""
        return cell.resource.request(priority=priority)

    def _release(self, cell: Cell):
        """Release the resource for a cell this vehicle holds."""
        for req in cell.resource.users:
            if getattr(req, "_vehicle", None) is self:
                cell.resource.release(req)
                return
        raise RuntimeError(f"Vehicle {self.id} does not hold {cell}")

    def _delayed_release(self, cell: Cell):
        """Release a cell after tau seconds (headway enforcement)."""
        def _release_process():
            yield self.env.timeout(self.tau)
            self._release(cell)
            cell.vehicle = None
            self._notify_neighbors_on_release(cell)
        self.env.process(_release_process())

    # ------------------------------------------------------------------
    # Movement process
    # ------------------------------------------------------------------

    def start(self):
        """Entry point: seize origin cell, then run movement + driver."""
        # Seize origin
        req = self._request(self.origin_cell)
        yield req
        req._vehicle = self
        self.cell = self.origin_cell
        self._cell_entry_time = self.env.now
        self.cell.vehicle = self
        self.speed = self.v_max
        self.active = True
        self.time_entered = self.env.now

        if self.destination_cell_idx is not None and self.origin_cell is not None:
            self.initial_distance = float(
                self.destination_cell_idx - self.origin_cell.idx
            )

        logger.debug(
            "t=%.2f  %s entered at %s, dest_cell=%s",
            self.env.now, self, self.origin_cell, self.destination_cell_idx,
        )

        self._record_trajectory()

        # Start concurrent driver process (AVs are driven externally by controller)
        if self.vtype == VehicleType.HDV:
            self._driver_proc = self.env.process(self._driver_process())

        # Run movement
        yield self.env.process(self._movement_process())

    def _movement_process(self):
        """Cell-by-cell movement: request -> wait -> seize -> delay -> release."""
        while self.active:
            if self._at_destination():
                yield self.env.process(self._exit())
                return

            target = self._resolve_next_target()
            if target is None:
                yield self.env.timeout(self.action_interval)
                continue

            yield self.env.process(self._advance_to(target))

    def _at_destination(self) -> bool:
        """Check if vehicle has reached its destination cell and lane."""
        return (
            self.destination_cell_idx is not None
            and self.cell.idx >= self.destination_cell_idx - 1
            and self.cell.lane.idx == self.destination_lane
        )

    def _resolve_next_target(self) -> Optional[Cell]:
        """Determine the next cell to move to, or None to wait.

        Handles stopped vehicles (lateral escape from blockage),
        end-of-lane exits, and blocked cells.
        """
        if self.speed <= 0:
            return self._try_lateral_escape()

        target = self._get_target_cell()
        if target is None:
            # End of lane — exit if near destination
            if (
                self.destination_cell_idx is None
                or self.cell.idx >= self.destination_cell_idx - 2
            ):
                # Signal caller to exit (handled via _at_destination on next iter)
                self.env.process(self._exit())
                return None
            return None

        if target.blocked:
            logger.debug(
                "t=%.2f  %s blocked ahead at %s, waiting",
                self.env.now, self, target,
            )
            return None

        return target

    def _try_lateral_escape(self) -> Optional[Cell]:
        """At speed 0, attempt a lateral move to escape a blockage.

        Forces an immediate direction re-evaluation so the vehicle doesn't
        have to wait for the next driver cycle to set a lateral direction.
        """
        if not self._near_blockage():
            return None
        # Force re-evaluation so we don't wait for the driver cycle
        if self.desired_direction == Direction.FORWARD:
            self._evaluate_direction()
        if self.desired_direction in (Direction.LEFT, Direction.RIGHT):
            lateral = self._get_target_cell()
            if lateral is not None and lateral != self.cell.next:
                logger.debug(
                    "t=%.2f  %s stopped but attempting lateral move → %s",
                    self.env.now, self, lateral,
                )
                self.speed = max(0.5, self.d)
                return lateral
        return None

    # Progressive traversal: below this speed (cells/s), cell crossing is
    # broken into sub-steps so the vehicle can react to driver speed updates
    # mid-cell. Above this threshold, a single timeout is used (fast path).
    _PROGRESSIVE_SPEED_THRESHOLD = 1.0  # ~27 km/h at 7.5m cells
    _TRAVERSAL_DT = 0.25               # sub-step duration (s)
    _LC_PATIENCE = 3.0                 # max seconds to wait for a lateral cell (s)
    _MIN_REEVAL_RATIO = 0.5  # fraction of tau used as min re-eval interval

    def _advance_to(self, target: Cell):
        """Request target cell, release current, travel, and register.

        For lateral moves (lane changes), a patience timeout applies:
        if the target cell is not acquired within _LC_PATIENCE seconds,
        the request is cancelled and the method returns False so the
        caller can retry with a different target.
        """
        is_lateral = (target != self.cell.next) if self.cell.next else False

        # Priority for cell requests (lower = higher priority in SimPy).
        # Vehicles escaping a blockage get priority proportional to how
        # long they have been waiting — longer wait → more urgent merge.
        if self._blockage_wait_since is not None:
            wait = self.env.now - self._blockage_wait_since
            priority = -(1.0 + wait)  # always < 0; grows with wait time
        else:
            priority = 0.0
        req = self._request(target, priority=priority)

        if is_lateral:
            # Patience timeout: cancel LC if gap doesn't open
            result = yield req | self.env.timeout(self._LC_PATIENCE)
            if req not in result:
                # Timed out — remove pending request from queue
                if req in target.resource.queue:
                    target.resource.queue.remove(req)
                self.count_lc_failures += 1
                self.desired_direction = Direction.FORWARD
                logger.debug(
                    "t=%.2f  %s LC patience expired for %s, reverting to FORWARD",
                    self.env.now, self, target,
                )
                return
        else:
            yield req  # Forward moves wait unconditionally

        req._vehicle = self

        old_cell = self.cell
        self._delayed_release(old_cell)

        if self.speed >= self._PROGRESSIVE_SPEED_THRESHOLD:
            # Fast path: single timeout for the whole cell
            yield self.env.timeout(1.0 / self.speed)
        else:
            # Slow path: progressive traversal reacts to speed changes mid-cell
            distance_remaining = 1.0  # 1 cell to cross
            while distance_remaining > 0:
                v = max(self.speed, 0.01)
                time_needed = distance_remaining / v
                if time_needed <= self._TRAVERSAL_DT:
                    yield self.env.timeout(time_needed)
                    break
                yield self.env.timeout(self._TRAVERSAL_DT)
                distance_remaining -= v * self._TRAVERSAL_DT

        # Detect speed limit change and interrupt driver for immediate re-eval
        old_limit = old_cell.speed_limit if old_cell else float("inf")
        new_limit = target.speed_limit

        self.cell = target
        self._cell_entry_time = self.env.now
        target.vehicle = self
        self._record_trajectory()

        # Notify nearby vehicles of this movement
        self._notify_neighbors(old_cell, is_lateral)

        if (old_limit != new_limit
                and self._driver_proc is not None
                and self._driver_proc.is_alive):
            self._driver_proc.interrupt()

    def wake_driver(self):
        """Wake the driver process for immediate re-evaluation.

        Called by other vehicles when they move into this vehicle's
        vicinity.  Skipped if the driver evaluated recently (within
        tau/2) to avoid redundant cascading wake-ups.
        """
        if self._wake_event is None or self._wake_event.triggered:
            return
        if self.env.now - self._last_eval_time < self.tau * self._MIN_REEVAL_RATIO:
            return
        self._wake_event.succeed()

    def _notify_neighbors(self, old_cell: Cell, is_lateral: bool):
        """Notify nearby vehicles after a movement.

        Scans the 3x3 grid around the new position.  Wake-up order
        depends on the movement type so the most affected vehicle
        (e.g. the new follower after a cut-in) reacts first.
        """
        c = self.cell
        if c is None:
            return

        if is_lateral:
            # Lateral move — the cut-in follower in the target lane is
            # most affected, then the old follower in the origin lane.
            ordered_cells = [
                c.previous,                          # new follower (cut-in)
                old_cell.previous if old_cell else None,  # old follower
                c.next,                              # new leader
                old_cell.next if old_cell else None,  # old leader
                c.left, c.right,                     # beside
                c.left_prev, c.left_next,            # far diagonals
                c.right_prev, c.right_next,          # far diagonals
            ]
        else:
            # Forward move — the follower behind benefits most (gap opened).
            ordered_cells = [
                c.previous,                          # follower (gap opened)
                c.left_prev, c.right_prev,           # behind-diagonal
                c.left, c.right,                     # beside
                c.next,                              # ahead
                c.left_next, c.right_next,           # ahead-diagonal
            ]

        for neighbor in ordered_cells:
            if neighbor is not None and neighbor.vehicle is not None:
                v = neighbor.vehicle
                if v is not self and v.active:
                    v.wake_driver()

    def _notify_neighbors_on_release(self, cell: Cell):
        """Notify nearby vehicles when a cell is freed (after tau).

        Vehicles adjacent to the freed cell may now have a merge
        opportunity or updated spacing.
        """
        ordered_cells = [
            cell.previous,
            cell.left, cell.right,
            cell.left_prev, cell.right_prev,
            cell.next,
            cell.left_next, cell.right_next,
        ]
        for neighbor in ordered_cells:
            if neighbor is not None and neighbor.vehicle is not None:
                v = neighbor.vehicle
                if v.active:
                    v.wake_driver()

    def _get_target_cell(self) -> Optional[Cell]:
        """Get the next cell based on desired direction."""
        if self.desired_direction == Direction.FORWARD:
            return self.cell.next
        elif self.desired_direction == Direction.LEFT:
            target = self.cell.left_next
            if target and not target.blocked and self._check_lc_safety(target):
                self.last_lc_time = self.env.now
                self.count_lane_changes += 1
                logger.debug(
                    "t=%.2f  %s lane change LEFT → %s", self.env.now, self, target,
                )
                return target
            return self.cell.next  # fallback to forward
        elif self.desired_direction == Direction.RIGHT:
            target = self.cell.right_next
            if target and not target.blocked and self._check_lc_safety(target):
                self.last_lc_time = self.env.now
                self.count_lane_changes += 1
                logger.debug(
                    "t=%.2f  %s lane change RIGHT → %s", self.env.now, self, target,
                )
                return target
            return self.cell.next  # fallback to forward
        return self.cell.next

    # Blockage detection range multiplier: drivers scan further ahead for
    # obstacles/incidents than for car-following (advance warning signs,
    # visible queues, etc.).  3× look_ahead ≈ 225m at 7.5m cells.
    _BLOCKAGE_SCAN_MULT = 3

    def _near_blockage(self) -> bool:
        """Check if there's a blockage ahead in the current lane."""
        if self.cell is None:
            return False
        scan = self.look_ahead * self._BLOCKAGE_SCAN_MULT
        return self.cell.find_blockage(scan) is not None

    def _check_lc_safety(self, target: Cell) -> bool:
        """Check front and rear gaps in target lane for lane change safety.

        Rear gap scales with the closing speed between the follower and
        this vehicle: high closing speed requires the full safety gap,
        zero closing speed requires only standstill spacing.  This allows
        merges in congested queues where everyone moves at similar speeds.

        Near a blockage, front gap is reduced to standstill spacing
        (urgent merge).
        """
        leader = target.find_leader(self.look_ahead)
        follower = target.find_follower(self.look_ahead)

        front_gap = float("inf")
        if leader and leader.cell is not None:
            front_gap = abs(leader.cell.idx - target.idx)

        rear_gap = float("inf")
        if follower and follower.cell is not None:
            rear_gap = abs(target.idx - follower.cell.idx)

        # Front gap: scales with closing speed to leader
        if leader and leader.cell is not None:
            closing_speed = max(0.0, self.speed - leader.speed)
            ratio = closing_speed / self.v_max
            req_front = self.d + (self.safety_gap_front - self.d) * ratio
        else:
            req_front = self.d  # no leader → standstill spacing suffices

        # Rear gap: scales with closing speed from follower
        if follower and follower.cell is not None:
            closing_speed = max(0.0, follower.speed - self.speed)
            ratio = closing_speed / self.v_max
            req_rear = self.d + (self.safety_gap_rear - self.d) * ratio
        else:
            req_rear = self.d  # no follower → standstill spacing suffices

        safe = front_gap >= req_front and rear_gap >= req_rear
        if not safe:
            self.count_lc_failures += 1
            logger.debug(
                "t=%.2f  %s LC safety FAIL at %s (front=%.0f rear=%.0f)",
                self.env.now, self, target, front_gap, rear_gap,
            )
        return safe

    def _exit(self):
        """Exit the freeway: release current cell after tau (outflow rate)."""
        logger.debug(
            "t=%.2f  %s exiting (travel_time=%.2fs)",
            self.env.now, self,
            self.env.now - self.time_entered if self.time_entered else 0,
        )
        self.time_exited = self.env.now
        self.active = False
        # Hold cell for tau seconds — enforces outflow capacity at boundary
        yield self.env.timeout(self.tau)
        self._release(self.cell)
        self.cell.vehicle = None
        self.cell = None

    # ------------------------------------------------------------------
    # Driver process (concurrent, decoupled from movement)
    # ------------------------------------------------------------------

    def _driver_process(self):
        """Periodically evaluate speed and direction.

        The driver waits for either the action_interval timeout or a
        wake-up event from a neighboring vehicle's movement, whichever
        comes first.  This makes drivers reactive in congestion (frequent
        neighbor movements) and relaxed in free flow (timeout dominates).

        Can also be interrupted (e.g. by a speed limit change) to force
        immediate re-evaluation.
        """
        while self.active:
            self._wake_event = self.env.event()
            self._last_eval_time = self.env.now
            self._evaluate_speed()
            self._evaluate_direction()
            try:
                yield self.env.timeout(self.action_interval) | self._wake_event
            except simpy.Interrupt:
                pass  # re-evaluate immediately on next loop iteration

    @property
    def fractional_position(self) -> float:
        """Estimate sub-cell position: cell_idx + fraction traversed.

        Uses elapsed time since cell entry and current speed to estimate
        how far through the current cell the vehicle has progressed.
        Returns a float like 42.3 meaning "30% through cell 42".
        """
        if self.cell is None:
            return 0.0
        dt = self.env.now - self._cell_entry_time
        frac = min(dt * self.speed, 1.0) if self.speed > 0 else 0.0
        return self.cell.idx + frac

    def _effective_v_max(self) -> float:
        """Vehicle top speed bounded by the current cell's speed limit."""
        if self.cell is not None:
            return min(self.v_max, self.cell.speed_limit)
        return self.v_max

    def _evaluate_speed(self):
        """Determine desired speed: blockage, car-following, or free-flow.

        When both a blockage and a leader exist, the closer constraint
        governs: a leader between the vehicle and the blockage means the
        vehicle follows the queue (creeping), while a direct view of the
        blockage means the vehicle decelerates for it.
        """
        if self.cell is None:
            return

        v_max = self._effective_v_max()

        scan = self.look_ahead * self._BLOCKAGE_SCAN_MULT
        blockage_dist = self.cell.find_blockage(scan)
        leader = self.cell.find_leader(self.look_ahead)

        # Track when vehicle first sees a blockage (for merge priority)
        if blockage_dist is not None:
            if self._blockage_wait_since is None:
                self._blockage_wait_since = self.env.now
        else:
            self._blockage_wait_since = None

        if blockage_dist is not None and leader is not None and leader.cell is not None:
            leader_dist = leader.fractional_position - self.fractional_position
            if leader_dist < 0:
                num_cells = self.cell.lane.num_cells
                leader_dist = (leader.cell.idx - self.cell.idx) % num_cells
            if leader_dist < blockage_dist:
                # Leader is closer than blockage — follow the queue
                self._speed_for_leader(leader, v_max)
            else:
                # Direct view of blockage — decelerate for it
                self._speed_for_blockage(blockage_dist, v_max)
            return

        if blockage_dist is not None:
            self._speed_for_blockage(blockage_dist, v_max)
            return

        if leader is not None and leader.cell is not None:
            self._speed_for_leader(leader, v_max)
            return

        # No constraints → free flow
        self._speed_free_flow(v_max)

    def _speed_for_blockage(self, blockage_dist: int, v_max: float):
        """Decelerate for a blocked cell ahead."""
        self.speed = newell.desired_speed(
            current_spacing=blockage_dist, leader_speed=0.0,
            tau=self.tau, d=self.d, v_max=v_max,
        )
        self.count_cf_evaluations += 1
        logger.debug(
            "t=%.2f  %s blockage ahead at %d cells → v=%.2f",
            self.env.now, self, blockage_dist, self.speed,
        )

    def _speed_for_leader(self, leader, v_max: float):
        """Newell car-following with fractional spacing."""
        spacing = leader.fractional_position - self.fractional_position
        if spacing < 0:
            # Wrap-around (ring road)
            num_cells = self.cell.lane.num_cells
            spacing = (leader.cell.idx - self.cell.idx) % num_cells

        self.speed = newell.desired_speed(
            current_spacing=spacing, leader_speed=leader.speed,
            tau=self.tau, d=self.d, v_max=v_max,
        )
        self.count_cf_evaluations += 1
        logger.debug(
            "t=%.2f  %s car-following: spacing=%.1f, leader_v=%.2f → v=%.2f",
            self.env.now, self, spacing, leader.speed, self.speed,
        )

    def _speed_free_flow(self, v_max: float):
        """Free-flow speed with optional stochastic slowdown."""
        base_speed = v_max
        if self.slowdown_prob > 0 and self.rng_slowdown.random() < self.slowdown_prob:
            base_speed = max(0.5, base_speed - self.slowdown_delta)
            self.count_slowdowns += 1
            logger.debug(
                "t=%.2f  %s random slowdown → v=%.2f",
                self.env.now, self, base_speed,
            )
        self.speed = base_speed

    def _evaluate_direction(self):
        """Determine desired direction: MLC, DLC, or forward."""
        if self.cell is None:
            return

        # Blockage ahead — forced MLC (bypass cooldown)
        # Use extended scan range (advance warning visibility)
        scan = self.look_ahead * self._BLOCKAGE_SCAN_MULT
        blockage_dist = self.cell.find_blockage(scan)
        if blockage_dist is not None:
            # The vehicle must leave its lane and eventually return:
            # +2 lane changes on top of any destination-driven need.
            num_lc = self._lane_changes_to_destination() + 2
            r = blockage_dist / scan  # 1.0 = far, 0.0 = imminent
            p = mlc_probability(r, num_lc, self.mlc_k, self.mlc_r0)
            if self.rng_mlc.random() < p:
                self.desired_direction = self._direction_away_from_blockage()
                return

        # Cooldown check
        if self.env.now - self.last_lc_time < self.dlc_cooldown:
            self.desired_direction = Direction.FORWARD
            return

        # MLC: do we need to reach the exit lane?
        num_lc_needed = self._lane_changes_to_destination()
        if num_lc_needed > 0:
            r = self._remaining_distance_ratio()
            p = mlc_probability(r, num_lc_needed, self.mlc_k, self.mlc_r0)
            if self.rng_mlc.random() < p:
                self.desired_direction = self._direction_toward_destination()
                return

        # DLC: speed incentive
        self._evaluate_dlc()

    def _evaluate_dlc(self):
        """Check if a discretionary lane change is beneficial.

        Suppresses DLC toward a lane that has a downstream blockage to
        prevent unrealistic congestion spillover: vehicles should not
        voluntarily move into a lane that feeds into an incident.
        """
        current_speed = self.speed
        scan = self.look_ahead * self._BLOCKAGE_SCAN_MULT

        # Check left
        if self.cell.left:
            # Suppress DLC toward a blocked lane
            if self.cell.left.find_blockage(scan) is None:
                left_leader = self.cell.left.find_leader(self.look_ahead)
                left_speed = left_leader.speed if left_leader else self.v_max
                p_left = dlc_probability(left_speed, current_speed, self.dlc_k, self.dlc_v0)
                if self.rng_dlc.random() < p_left:
                    self.desired_direction = Direction.LEFT
                    return

        # Check right
        if self.cell.right:
            if self.cell.right.find_blockage(scan) is None:
                right_leader = self.cell.right.find_leader(self.look_ahead)
                right_speed = right_leader.speed if right_leader else self.v_max
                p_right = dlc_probability(right_speed, current_speed, self.dlc_k, self.dlc_v0)
                if self.rng_dlc.random() < p_right:
                    self.desired_direction = Direction.RIGHT
                    return

        self.desired_direction = Direction.FORWARD

    def _lane_changes_to_destination(self) -> int:
        """Number of lane changes needed to reach destination lane."""
        if self.cell is None or self.destination_cell_idx is None:
            return 0
        return abs(self.cell.lane.idx - self.destination_lane)

    def _remaining_distance_ratio(self) -> float:
        """Fraction of trip remaining (1.0 at origin, 0.0 at destination)."""
        if (
            self.cell is None
            or self.destination_cell_idx is None
            or self.initial_distance is None
            or self.initial_distance <= 0
        ):
            return 1.0
        remaining = max(0, self.destination_cell_idx - self.cell.idx)
        return min(1.0, remaining / self.initial_distance)

    def _direction_toward_destination(self) -> Direction:
        """Which direction to go to approach destination lane."""
        if self.cell is None:
            return Direction.FORWARD
        current_lane = self.cell.lane.idx
        if self.destination_lane < current_lane:
            return Direction.RIGHT
        elif self.destination_lane > current_lane:
            return Direction.LEFT
        return Direction.FORWARD

    def _direction_away_from_blockage(self) -> Direction:
        """Pick a direction to escape a blocked lane.

        Prefer the lane with more open space. If both are available,
        prefer right (toward slower lanes, conventional merging).
        """
        if self.cell is None:
            return Direction.FORWARD
        has_right = self.cell.right is not None
        has_left = self.cell.left is not None
        # Check if adjacent lanes are also blocked at the same position
        if has_right and self.cell.right.find_blockage(self.look_ahead) is None:
            return Direction.RIGHT
        if has_left and self.cell.left.find_blockage(self.look_ahead) is None:
            return Direction.LEFT
        # Both blocked or unavailable — try any available
        if has_right:
            return Direction.RIGHT
        if has_left:
            return Direction.LEFT
        return Direction.FORWARD

    # ------------------------------------------------------------------
    # Trajectory recording
    # ------------------------------------------------------------------

    def _record_trajectory(self):
        """Record T(x, n) entry."""
        if self.cell is None:
            return
        self.trajectory.append(TrajectoryRecord(
            time=self.env.now,
            cell_idx=self.cell.idx,
            lane_idx=self.cell.lane.idx,
            speed=self.speed,
        ))

    def __repr__(self):
        lane = self.cell.lane.idx if self.cell else "?"
        pos = self.cell.idx if self.cell else "?"
        return f"{self.vtype.value.upper()}({self.id}, L{lane}@{pos}, v={self.speed:.1f})"
