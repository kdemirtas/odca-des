"""Vehicle: the physical side of a vehicle in ODCA-DES (D-2026-09-19-24, D-2026-09-19-30).

A vehicle is a SimPy process that moves cell by cell through the freeway with the
request-wait-seize-delay-release protocol: it takes the next cell, crosses its current cell at
its speed, and releases the cell it left tau seconds later. Its driver (`odca.entity.driver`)
decides the speed and the direction; the vehicle carries them out.

The link contract: the driver reads the vehicle's state and its neighbours through cells, and
changes the vehicle only through `set_target_speed` and `request_direction`. The vehicle calls
its driver to wake it, to make it react now, to judge a gap or a blockage, and reads its tau,
action interval, lane-change patience and merge priority.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, List, Optional

import simpy

from odca.infrastructure.cell import Cell
from odca.params import VehicleConfig

if TYPE_CHECKING:
    from odca.entity.driver import Driver
    from odca.infrastructure.freeway import Destination

logger = logging.getLogger(__name__)


class Direction(Enum):
    FORWARD = "forward"
    LEFT = "left"
    RIGHT = "right"


@dataclass
class TrajectoryRecord:
    """A single passage-time record: T(x, n)."""
    time: float          # T_arr: the vehicle is in this cell from here
    acquired: float      # T_acq: it took the cell here and crossed into it by T_arr
    cell_idx: int
    lane_idx: int
    speed: float
    v_free: float  # the speed this vehicle could hold on this cell alone (D-2026-09-20-3)


class Vehicle:
    """One vehicle: position, cell lock, movement, exit and trajectory."""

    _id_counter = 0

    def __init__(self, env: simpy.Environment, cfg: VehicleConfig, driver: Driver,
                 origin_cell: Cell, destination: Optional[Destination] = None):
        """A vehicle waiting to enter at `origin_cell`, linked both ways with `driver`.

        Args:
            env: the SimPy environment.
            cfg: top speed, jam spacing and movement resolution.
            driver: who decides for this vehicle; it is attached here.
            origin_cell: the road cell it enters at.
            destination: where it leaves; None drives on until the road ends (a ring never ends).
        """
        self.id = Vehicle._id_counter
        Vehicle._id_counter += 1
        self.env = env
        self.cfg = cfg

        # Route
        self.origin_cell = origin_cell
        self.destination_cell_idx: Optional[int] = None
        self.destination_lane: Optional[int] = None
        if destination is not None:
            self.destination_cell_idx = destination.cell_idx
            self.destination_lane = destination.lane
        self.initial_distance: Optional[float] = None
        self.route_start_idx: int = origin_cell.idx

        # State
        self.cell: Optional[Cell] = None
        self._cell_entry_time: float = 0.0  # when current cell was entered
        self.speed: float = 0.0
        self.desired_direction: Direction = Direction.FORWARD
        self.active: bool = False
        self.last_lc_time: float = -999.0

        # Trajectory log: the T(x, n) output
        self.trajectory: List[TrajectoryRecord] = []

        # Entry/exit times; created is when the generator released it, entered when it got
        # onto the road, so the gap is the wait at the origin (D-2026-09-20-5)
        self.time_created: float = env.now
        self.time_entered: Optional[float] = None
        self.time_exited: Optional[float] = None


        # Movement counters; the driver counts its decisions
        self.count_lane_changes: int = 0
        self.count_lc_failures: int = 0  # lateral requests not granted within the patience
        self.count_missed_exits: int = 0

        self.driver = driver
        driver.attach(self)

    @property
    def kind(self) -> str:
        """What drives this vehicle: `human` or `autonomous`."""
        return self.driver.kind

    # ------------------------------------------------------------------
    # Commands from the driver
    # ------------------------------------------------------------------

    def set_target_speed(self, speed: float):
        """Drive at `speed` (cells/s) from now on.

        Args:
            speed: the driver's chosen speed.
        """
        self.speed = speed

    def request_direction(self, direction: Direction):
        """Move forward, or change lanes at the next move if the gap allows.

        Args:
            direction: where the driver wants to go.
        """
        self.desired_direction = direction

    # ------------------------------------------------------------------
    # Resource protocol
    # ------------------------------------------------------------------

    def _request(self, cell: Cell, priority: float = 0.0):
        """Create a PriorityResource request for a cell."""
        return cell.resource.request(priority=priority)

    def _acquired_at(self, cell: Cell) -> float:
        """When this vehicle took `cell`, the T_acq of the protocol (D-2026-09-20-5).

        Args:
            cell: a cell this vehicle holds.
        """
        for req in cell.resource.users:
            if getattr(req, "_vehicle", None) is self:
                return getattr(req, "_acquired", self.env.now)
        return self.env.now

    def _release(self, cell: Cell):
        """Release the resource for a cell this vehicle holds."""
        for req in cell.resource.users:
            if getattr(req, "_vehicle", None) is self:
                cell.resource.release(req)
                return
        raise RuntimeError(f"Vehicle {self.id} does not hold {cell}")

    def _delayed_release(self, cell: Cell):
        """Release a cell's resource tau seconds after the next cell is taken (headway).

        Releases the lock only; the cell's position label changes in _on_cell_change.
        """
        def _release_process():
            yield self.env.timeout(self.driver.tau)
            self._release(cell)
            self._notify_neighbors_on_release(cell)
        self.env.process(_release_process())

    def _on_cell_change(self, new_cell: Optional[Cell], limit_changed: bool = False):
        """The one place a vehicle's position changes (D-2026-09-19-12).

        `self.cell` and `cell.vehicle` are both position: they change together, at arrival in
        a cell, or at leaving the network (new_cell None). The resource lock is separate
        (`cell.is_occupied`) and follows delayed release.

        Args:
            new_cell: the cell just arrived in, or None when the vehicle leaves the network.
            limit_changed: the new cell posts a different speed limit, so the driver picks the
                speed again before this cell is crossed (D-2026-09-20-4).
        """
        old_cell = self.cell
        if old_cell is not None and old_cell.vehicle is self:
            old_cell.vehicle = None
        self.cell = new_cell
        if new_cell is None:
            return
        new_cell.vehicle = self
        self._cell_entry_time = self.env.now
        if limit_changed:
            self.driver.evaluate_speed()
        self._record_trajectory()

    # ------------------------------------------------------------------
    # Movement process
    # ------------------------------------------------------------------

    def start(self):
        """Entry point: seize origin cell, then run movement + driver.

        A metered origin (an `OriginCell` with a speed limit, D-2026-09-19-27) is passed first.
        """
        meter = self.origin_cell.entry
        metered = meter is not None and meter.limited
        if metered:
            meter_req = self._request(meter)
            yield meter_req
            meter_req._vehicle = self
            meter_req._acquired = self.env.now
            yield self.env.timeout(1.0 / min(self.cfg.v_max, meter.speed_limit))
        # Seize origin
        req = self._request(self.origin_cell)
        yield req
        req._vehicle = self
        req._acquired = self.env.now
        if metered:
            self._delayed_release(meter)
        self.speed = self.cfg.v_max
        self.active = True
        self.time_entered = self.env.now
        self._on_cell_change(self.origin_cell)

        if self.destination_cell_idx is not None:
            self.initial_distance = float(self.destination_cell_idx - self.origin_cell.idx)

        logger.debug(
            "t=%.2f  %s entered at %s, dest_cell=%s",
            self.env.now, self, self.origin_cell, self.destination_cell_idx,
        )

        self.driver.start()
        yield self.env.process(self._movement_process())

    def _movement_process(self):
        """Cell-by-cell movement: request -> wait -> seize -> delay -> release."""
        while self.active:
            if self._at_destination():
                yield self.env.process(self._exit())
                return
            if self._passed_exit():
                self._retarget_missed_exit()

            target = self._resolve_next_target()
            if target is None:
                if self.cell.next is None:  # end of the road: the only other way out
                    if self.destination_lane not in (None, self.cell.lane.idx):
                        self.count_missed_exits += 1  # its end lane not reached (D-2026-09-19-26)
                    yield self.env.process(self._exit())
                    return
                yield self.env.timeout(self.driver.action_interval)
                continue

            yield self.env.process(self._advance_to(target))

    def _passed_exit(self) -> bool:
        """Whether the vehicle drove past its off-ramp without reaching the exit lane."""
        return (
            self.destination_lane is not None
            and self.destination_cell_idx is not None
            and self.cell.idx > self.destination_cell_idx
        )

    def _retarget_missed_exit(self):
        """Take the next off-ramp downstream, or the segment end from any lane (D-2026-09-19-17)."""
        freeway = self.cell.lane.freeway
        later_ramps = [d for d in freeway.destinations.values()
                       if d.is_offramp and d.cell_idx > self.cell.idx]
        if later_ramps:
            ramp = min(later_ramps, key=lambda d: d.cell_idx)
            self.destination_cell_idx, self.destination_lane = ramp.cell_idx, ramp.lane
        else:
            self.destination_cell_idx = freeway.num_cells
            self.destination_lane = None
        self.route_start_idx = self.cell.idx
        self.count_missed_exits += 1

    def _at_destination(self) -> bool:
        """Check if vehicle has reached its destination cell and lane."""
        return (
            self.destination_cell_idx is not None
            and self.cell.idx >= self.destination_cell_idx - 1
            and (self.destination_lane is None or self.cell.lane.idx == self.destination_lane)
        )

    def _resolve_next_target(self) -> Optional[Cell]:
        """Determine the next cell to move to, or None to wait.

        Handles stopped vehicles (lateral escape from blockage),
        end-of-lane exits, and blocked cells.
        """
        if self.speed <= 0:
            return self._try_lateral_escape()

        target = self._target_cell()
        if target is None:
            return None  # end of the road: the movement loop exits

        if target.blocked:
            logger.debug(
                "t=%.2f  %s blocked ahead at %s, waiting",
                self.env.now, self, target,
            )
            return None

        return target

    def _try_lateral_escape(self) -> Optional[Cell]:
        """At speed 0, attempt a lateral move to escape a blockage.

        Asks the driver for a direction at once, so the vehicle does not wait for the next
        decision to move sideways.
        """
        if not self.driver.sees_blockage():
            return None
        if self.desired_direction == Direction.FORWARD:
            self.driver.evaluate_direction()
        if self.desired_direction in (Direction.LEFT, Direction.RIGHT):
            lateral = self._target_cell()
            if lateral is not None and lateral != self.cell.next:
                logger.debug(
                    "t=%.2f  %s stopped but attempting lateral move → %s",
                    self.env.now, self, lateral,
                )
                self.speed = self.cfg.escape_speed
                return lateral
        return None

    def _advance_to(self, target: Cell):
        """Request target cell, release current, travel, and register.

        A lateral move (lane change) waits at most the driver's lane-change patience for the
        target cell; if it is not granted by then, the request is withdrawn and the vehicle
        goes back to FORWARD.
        """
        is_lateral = (target != self.cell.next) if self.cell.next else False

        # lower is served first; a driver waiting behind a blockage merges with urgency
        req = self._request(target, priority=self.driver.merge_priority())

        if is_lateral:
            result = yield req | self.env.timeout(self.driver.lc_patience)
            if req not in result:
                if req.triggered:
                    # granted in the same instant the patience ran out: give the cell back
                    target.resource.release(req)
                else:
                    req.cancel()
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
        req._acquired = self.env.now
        if is_lateral:
            # a lane change counts, and its cooldown starts, once it happens (D-2026-09-19-18);
            # the request is used up: one decision, one lane change (D-2026-09-19-31)
            self.last_lc_time = self.env.now
            self.count_lane_changes += 1
            self.desired_direction = Direction.FORWARD

        old_cell = self.cell
        self._delayed_release(old_cell)

        if self.speed >= self.cfg.progressive_speed_threshold:
            # Fast path: single timeout for the whole cell
            yield self.env.timeout(1.0 / self.speed)
        else:
            # Slow path: progressive traversal reacts to speed changes mid-cell
            step = self.cfg.traversal_dt
            distance_remaining = 1.0  # 1 cell to cross
            while distance_remaining > 0:
                v = max(self.speed, 0.01)
                time_needed = distance_remaining / v
                if time_needed <= step:
                    yield self.env.timeout(time_needed)
                    break
                yield self.env.timeout(step)
                distance_remaining -= v * step

        old_limit = old_cell.speed_limit if old_cell else float("inf")

        self._on_cell_change(target, limit_changed=target.speed_limit != old_limit)

        # Notify nearby vehicles of this movement
        self._notify_neighbors(old_cell, is_lateral)

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
            # Lateral move: the cut-in follower in the target lane is
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
            # Forward move: the follower behind benefits most (gap opened).
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
                    v.driver.wake()

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
                    v.driver.wake()

    def _target_cell(self) -> Optional[Cell]:
        """The next cell for the requested direction; forward when the gap is refused."""
        if self.desired_direction == Direction.FORWARD:
            return self.cell.next
        target = (self.cell.left_next if self.desired_direction == Direction.LEFT
                  else self.cell.right_next)
        if target and not target.blocked and self.driver.accepts_gap(target):
            logger.debug(
                "t=%.2f  %s lane change %s → %s",
                self.env.now, self, self.desired_direction.name, target,
            )
            return target
        return self.cell.next

    def _exit_cell(self):
        """The destination cell this vehicle leaves into from its current cell, if any."""
        for exit_cell in self.cell.exits:
            dest = exit_cell.destination
            if dest.cell_idx == self.destination_cell_idx and dest.lane == self.destination_lane:
                return exit_cell
        return None

    def _exit(self):
        """Exit the freeway: release current cell after tau (outflow rate).

        A throttled destination (a `DestinationCell` with a speed limit, D-2026-09-19-27) is
        entered like a road cell: the vehicle takes it, passes it at the limit, and holds it
        for tau after leaving.
        """
        exit_cell = self._exit_cell()
        if exit_cell is not None and exit_cell.limited:
            yield self.env.process(self._exit_through(exit_cell))
            return
        logger.debug(
            "t=%.2f  %s exiting (travel_time=%.2fs)",
            self.env.now, self,
            self.env.now - self.time_entered if self.time_entered else 0,
        )
        self.time_exited = self.env.now
        self.active = False
        # Hold cell for tau seconds: enforces outflow capacity at boundary
        yield self.env.timeout(self.driver.tau)
        self._release(self.cell)
        self._on_cell_change(None)

    def _exit_through(self, exit_cell):
        """Leave through a throttled destination cell.

        Args:
            exit_cell: the limited `DestinationCell`.
        """
        req = self._request(exit_cell)
        yield req
        req._vehicle = self
        req._acquired = self.env.now
        self._delayed_release(self.cell)
        speed = min(self.speed, exit_cell.speed_limit) if self.speed > 0 else exit_cell.speed_limit
        yield self.env.timeout(1.0 / speed)
        self.time_exited = self.env.now
        self.active = False
        self._on_cell_change(None)
        yield self.env.timeout(self.driver.tau)
        self._release(exit_cell)

    # ------------------------------------------------------------------
    # State the driver reads
    # ------------------------------------------------------------------

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

    def effective_v_max(self) -> float:
        """Free-flow speed here: the vehicle's top speed capped by the cell's limit.

        This is v_f(n, c) of the delay definition (D-2026-09-20-3): what this vehicle would
        hold on this cell with no other vehicle in the way. A work zone lowers it; other
        traffic does not.
        """
        if self.cell is not None:
            return min(self.cfg.v_max, self.cell.speed_limit)
        return self.cfg.v_max

    # ------------------------------------------------------------------
    # Trajectory recording
    # ------------------------------------------------------------------

    def _record_trajectory(self):
        """Record T(x, n) entry."""
        if self.cell is None:
            return
        self.trajectory.append(TrajectoryRecord(
            time=self.env.now,
            acquired=self._acquired_at(self.cell),
            cell_idx=self.cell.idx,
            lane_idx=self.cell.lane.idx,
            speed=self.speed,
            v_free=self.effective_v_max(),
        ))

    def __repr__(self):
        lane = self.cell.lane.idx if self.cell else "?"
        pos = self.cell.idx if self.cell else "?"
        return f"{self.kind}({self.id}, L{lane}@{pos}, v={self.speed:.1f})"
