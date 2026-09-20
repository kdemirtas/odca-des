"""Drivers: who decides a vehicle's speed and direction (D-2026-09-19-24, D-2026-09-19-30).

`Driver` holds the decisions: target speed (Newell car following, blockages, random slowdown),
direction (logistic MLC and DLC over the exposure since the last decision, D-2026-09-19-22),
gap acceptance, and the decision state. `HumanDriver` decides in its own SimPy process, woken
early when a neighbour moves; `AutonomousDriver` is called by its `AutonomousController`. A
driver changes its vehicle only through `set_target_speed` and `request_direction`.

A human driver population (`HumanDriverConfig`) gives means and spreads; each driver's own
values are drawn once, when the vehicle is created: tau and action interval log-normal (always
positive, right-skewed for the occasional slow driver), slowdown probability normal clipped to
[0, 1]. Each draw has its own stream, shared by all drivers, used in that order; a value whose
spread is 0 is not drawn (its stream is not advanced).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, ClassVar, Optional

import numpy as np
import simpy

from odca.entity.vehicle import Direction
from odca.infrastructure.cell import Cell
from odca.models.car_following import newell
from odca.models.lane_changing.discretionary import dlc_probability
from odca.models.lane_changing.mandatory import MLC_REFERENCE_CELLS, mlc_probability
from odca.models.lane_changing.rate import probability_over
from odca.params import AutonomousDriverConfig, DriverConfig, HumanDriverConfig
from odca.rng import RNGRegistry

if TYPE_CHECKING:
    from odca.entity.controller import AutonomousController
    from odca.entity.vehicle import Vehicle

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class DriverTraits:
    """One driver's own values."""

    tau: float               # reaction time (s)
    action_interval: float   # time between decisions (s)
    slowdown_prob: float     # chance of a random slowdown per decision

    @classmethod
    def exact(cls, cfg: DriverConfig) -> DriverTraits:
        """The config's values, undrawn (autonomous drivers).

        Args:
            cfg: a driver config.
        """
        return cls(cfg.tau, cfg.action_interval, cfg.slowdown_prob)


def _lognormal(rng: np.random.Generator, mean: float, std: float) -> float:
    """A log-normal draw with the given mean and standard deviation.

    Args:
        rng: the stream.
        mean: mean of the draw.
        std: standard deviation of the draw.
    """
    sigma_ln2 = np.log(1 + (std / mean) ** 2)
    mu_ln = np.log(mean) - sigma_ln2 / 2
    return rng.lognormal(mu_ln, np.sqrt(sigma_ln2))


class TraitSampler:
    """Draws human drivers' traits from three streams: tau, action interval, slowdown."""

    def __init__(self, tau: np.random.Generator, action_interval: np.random.Generator,
                 slowdown_prob: np.random.Generator):
        """A sampler on three streams.

        Args:
            tau: stream for reaction times.
            action_interval: stream for action intervals.
            slowdown_prob: stream for slowdown probabilities.
        """
        self.rng_tau = tau
        self.rng_action_interval = action_interval
        self.rng_slowdown_prob = slowdown_prob

    @classmethod
    def spawn(cls, registry: RNGRegistry) -> TraitSampler:
        """A sampler on three new streams of `registry`, spawned in the fixed order.

        Args:
            registry: the run's RNG registry.
        """
        return cls(registry.spawn("driver_tau"), registry.spawn("driver_action_interval"),
                   registry.spawn("driver_slowdown_param"))

    def draw(self, cfg: HumanDriverConfig) -> DriverTraits:
        """One driver's traits.

        Args:
            cfg: the population: means, spreads and clipping ranges.
        """
        tau, action_interval, slowdown_prob = cfg.tau, cfg.action_interval, cfg.slowdown_prob
        if cfg.tau_std > 0:
            tau = float(np.clip(_lognormal(self.rng_tau, cfg.tau, cfg.tau_std),
                                cfg.tau_min, cfg.tau_max))
        if cfg.action_interval_std > 0:
            drawn = _lognormal(self.rng_action_interval, cfg.action_interval,
                               cfg.action_interval_std)
            action_interval = float(np.clip(drawn, cfg.action_interval_min,
                                            cfg.action_interval_max))
        if cfg.slowdown_prob_std > 0:
            drawn = self.rng_slowdown_prob.normal(cfg.slowdown_prob, cfg.slowdown_prob_std)
            slowdown_prob = float(np.clip(drawn, 0.0, 1.0))
        return DriverTraits(tau, action_interval, slowdown_prob)


@dataclass(frozen=True, slots=True)
class DriverStreams:
    """The decision streams every driver shares: random slowdown, MLC and DLC draws."""

    slowdown: np.random.Generator
    mlc: np.random.Generator
    dlc: np.random.Generator

    @classmethod
    def spawn(cls, registry: RNGRegistry) -> DriverStreams:
        """Three new streams of `registry`, spawned in the fixed order.

        Args:
            registry: the run's RNG registry.
        """
        return cls(registry.spawn("slowdown"), registry.spawn("mlc"), registry.spawn("dlc"))


class Driver:
    """The decisions for one vehicle; the subclasses say when they are made."""

    kind: ClassVar[str]

    def __init__(self, cfg: DriverConfig, streams: DriverStreams,
                 traits: Optional[DriverTraits] = None):
        """A driver not yet attached to a vehicle.

        Args:
            cfg: the driver config (population values for humans).
            streams: the shared decision streams.
            traits: this driver's own values; None takes the config's exactly.
        """
        traits = traits or DriverTraits.exact(cfg)
        lane_change = cfg.lane_change
        self.cfg = cfg
        self.streams = streams
        self.vehicle: Optional[Vehicle] = None
        self.env: Optional[simpy.Environment] = None
        self.tau = traits.tau
        self.action_interval = traits.action_interval
        self.slowdown_prob = traits.slowdown_prob
        self.slowdown_delta = cfg.slowdown_delta
        self.look_ahead = cfg.look_ahead
        self.blockage_scan = cfg.look_ahead * cfg.blockage_scan_mult
        self.lc_patience = cfg.lc_patience
        self.lane_change = lane_change
        self.dlc_enabled = lane_change.dlc_enabled

        # decision state
        self._blockage_wait_since: Optional[float] = None  # first saw the blockage ahead
        # exposure since the last direction evaluation: time for DLC, distance for MLC
        self._last_direction_eval_time: Optional[float] = None
        self._last_direction_eval_position: Optional[float] = None

        # decision counters; the vehicle counts its moves
        self.count_slowdowns = 0
        self.count_cf_evaluations = 0
        self.count_speed_evaluations = 0
        self.count_gap_rejections = 0

    def attach(self, vehicle: Vehicle):
        """Link this driver to the vehicle it drives (called by `Vehicle`).

        Args:
            vehicle: the vehicle.
        """
        self.vehicle = vehicle
        self.env = vehicle.env
        self._d = vehicle.cfg.standstill_spacing
        self._v_max = vehicle.cfg.v_max

    # ------------------------------------------------------------------
    # Calls from the vehicle
    # ------------------------------------------------------------------

    def start(self):
        """The vehicle has entered the road."""

    def wake(self):
        """A neighbour moved or freed a cell."""

    def merge_priority(self) -> float:
        """Request priority for the next cell: lower is served first, growing with the wait
        behind a blockage."""
        if self._blockage_wait_since is None:
            return 0.0
        return -(1.0 + self.env.now - self._blockage_wait_since)

    def sees_blockage(self) -> bool:
        """Whether a blockage is in view ahead in the current lane."""
        cell = self.vehicle.cell
        return cell is not None and cell.find_blockage(self.blockage_scan) is not None

    def accepts_gap(self, target: Cell) -> bool:
        """Whether the front and rear gaps at `target` are safe to change lanes into.

        The required gap grows from the jam spacing to the safety gap with the closing speed
        (to the leader in front, from the follower behind), so vehicles merge in slow queues.

        Args:
            target: the cell in the next lane.
        """
        vehicle = self.vehicle
        if target.vehicle is not None or target.is_occupied:
            # find_leader and find_follower start one cell away, so the target's own
            # occupant (position) and lock holder are checked here (D-2026-09-19-13)
            self.count_gap_rejections += 1
            return False

        leader = target.find_leader(self.look_ahead)
        follower = target.find_follower(self.look_ahead)
        d = self._d

        front_gap = float("inf")
        req_front = d  # no leader: standstill spacing suffices
        if leader and leader.cell is not None:
            front_gap = abs(leader.cell.idx - target.idx)
            ratio = max(0.0, vehicle.speed - leader.speed) / self._v_max
            req_front = d + (self.lane_change.safety_gap_front - d) * ratio

        rear_gap = float("inf")
        req_rear = d
        if follower and follower.cell is not None:
            rear_gap = abs(target.idx - follower.cell.idx)
            ratio = max(0.0, follower.speed - vehicle.speed) / self._v_max
            req_rear = d + (self.lane_change.safety_gap_rear - d) * ratio

        safe = front_gap >= req_front and rear_gap >= req_rear
        if not safe:
            self.count_gap_rejections += 1
            logger.debug(
                "t=%.2f  %s LC safety FAIL at %s (front=%.0f rear=%.0f)",
                self.env.now, vehicle, target, front_gap, rear_gap,
            )
        return safe

    # ------------------------------------------------------------------
    # Decisions
    # ------------------------------------------------------------------

    def decide(self):
        """Choose the speed, then the direction."""
        self.evaluate_speed()
        self.evaluate_direction()

    def evaluate_speed(self):
        """Choose the speed: blockage, car following, or free flow.

        When both a blockage and a leader exist, the closer constraint
        governs: a leader between the vehicle and the blockage means the
        vehicle follows the queue (creeping), while a direct view of the
        blockage means the vehicle decelerates for it.
        """
        vehicle = self.vehicle
        cell = vehicle.cell
        if cell is None:
            return
        self.count_speed_evaluations += 1

        v_max = vehicle.effective_v_max()
        blockage_dist = cell.find_blockage(self.blockage_scan)
        leader = cell.find_leader(self.look_ahead)

        # Track when vehicle first sees a blockage (for merge priority)
        if blockage_dist is not None:
            if self._blockage_wait_since is None:
                self._blockage_wait_since = self.env.now
        else:
            self._blockage_wait_since = None

        if blockage_dist is not None and leader is not None and leader.cell is not None:
            leader_dist = leader.fractional_position - vehicle.fractional_position
            if leader_dist < 0:
                leader_dist = (leader.cell.idx - cell.idx) % cell.lane.num_cells
            if leader_dist < blockage_dist:
                # Leader is closer than blockage: follow the queue
                self._speed_for_leader(leader, v_max)
            else:
                # Direct view of blockage: decelerate for it
                self._speed_for_blockage(blockage_dist, v_max)
            return

        if blockage_dist is not None:
            self._speed_for_blockage(blockage_dist, v_max)
            return

        if leader is not None and leader.cell is not None:
            self._speed_for_leader(leader, v_max)
            return

        self._speed_free_flow(v_max)

    def _speed_for_blockage(self, blockage_dist: int, v_max: float):
        """Decelerate for a blocked cell ahead.

        Args:
            blockage_dist: cells to the blocked cell.
            v_max: the top speed here.
        """
        speed = newell.desired_speed(
            current_spacing=blockage_dist, leader_speed=0.0,
            tau=self.tau, d=self._d, v_max=v_max,
        )
        self.vehicle.set_target_speed(speed)
        self.count_cf_evaluations += 1
        logger.debug(
            "t=%.2f  %s blockage ahead at %d cells → v=%.2f",
            self.env.now, self.vehicle, blockage_dist, speed,
        )

    def _speed_for_leader(self, leader: Vehicle, v_max: float):
        """Newell car following with fractional spacing.

        Args:
            leader: the vehicle ahead in this lane.
            v_max: the top speed here.
        """
        vehicle = self.vehicle
        spacing = leader.fractional_position - vehicle.fractional_position
        if spacing < 0:
            # Wrap-around (ring road)
            spacing = (leader.cell.idx - vehicle.cell.idx) % vehicle.cell.lane.num_cells

        speed = newell.desired_speed(
            current_spacing=spacing, leader_speed=leader.speed,
            tau=self.tau, d=self._d, v_max=v_max,
        )
        # Newell gives 0 below the jam spacing; behind a moving leader with room ahead the
        # vehicle creeps, so the spacing can grow instead of freezing
        if speed <= 0 and leader.speed > 0 and spacing > 0:
            speed = self.cfg.min_creep_speed
        vehicle.set_target_speed(speed)

        self.count_cf_evaluations += 1
        logger.debug(
            "t=%.2f  %s car-following: spacing=%.1f, leader_v=%.2f → v=%.2f",
            self.env.now, vehicle, spacing, leader.speed, speed,
        )

    def _speed_free_flow(self, v_max: float):
        """Free-flow speed with optional stochastic slowdown.

        Args:
            v_max: the top speed here.
        """
        speed = v_max
        if self.slowdown_prob > 0 and self.streams.slowdown.random() < self.slowdown_prob:
            speed = max(self.cfg.slowdown_min_speed, speed - self.slowdown_delta)
            self.count_slowdowns += 1
            logger.debug(
                "t=%.2f  %s random slowdown → v=%.2f",
                self.env.now, self.vehicle, speed,
            )
        self.vehicle.set_target_speed(speed)

    def _direction_exposure(self):
        """Seconds and cells since the previous direction evaluation (0, 0 on the first).

        The lane-change curves give a probability per 5.2 cells driven (MLC) or per second
        (DLC), so each evaluation converts them over the exposure since the last one; how
        often a vehicle evaluates no longer changes how often it changes lanes (D-2026-09-19-22).
        """
        now, position = self.env.now, self.vehicle.fractional_position
        if self._last_direction_eval_time is None:
            elapsed, driven = 0.0, 0.0
        else:
            elapsed = now - self._last_direction_eval_time
            driven = max(0.0, position - self._last_direction_eval_position)
        self._last_direction_eval_time, self._last_direction_eval_position = now, position
        return elapsed, driven

    def evaluate_direction(self):
        """Choose the direction: MLC, DLC, or forward."""
        vehicle = self.vehicle
        if vehicle.cell is None:
            return
        elapsed, driven = self._direction_exposure()
        mlc_exposure = driven / MLC_REFERENCE_CELLS
        lc = self.lane_change

        # Blockage ahead: forced MLC (bypasses the cooldown), seen from further away
        scan = self.blockage_scan
        blockage_dist = vehicle.cell.find_blockage(scan)
        if blockage_dist is not None:
            # The vehicle must leave its lane and eventually return:
            # +2 lane changes on top of any destination-driven need.
            num_lc = self._lane_changes_to_destination() + 2
            r = blockage_dist / scan  # 1.0 = far, 0.0 = imminent
            p = probability_over(mlc_probability(r, num_lc, lc.mlc_k, lc.mlc_r0), mlc_exposure)
            if self.streams.mlc.random() < p:
                vehicle.request_direction(self._direction_away_from_blockage())
                return

        # MLC: do we need to reach the exit lane?
        num_lc_needed = self._lane_changes_to_destination()
        if num_lc_needed > 0:
            r = self._remaining_distance_ratio()
            p = probability_over(mlc_probability(r, num_lc_needed, lc.mlc_k, lc.mlc_r0),
                                 mlc_exposure)
            if self.streams.mlc.random() < p:
                vehicle.request_direction(self._direction_toward_destination())
                return

        # DLC: speed incentive (off for centrally controlled vehicles); the cooldown
        # applies to discretionary changes only (manuscript tex:352, D-2026-09-19-18)
        if self.dlc_enabled and self.env.now - vehicle.last_lc_time >= lc.dlc_cooldown:
            vehicle.request_direction(self._dlc_direction(elapsed))
        else:
            vehicle.request_direction(Direction.FORWARD)

    def _dlc_direction(self, elapsed: float) -> Direction:
        """Left or right if a discretionary lane change there is drawn, else forward.

        A lane with a blockage ahead is never chosen: vehicles should not move into a lane
        that feeds an incident.

        Args:
            elapsed: seconds since the previous direction evaluation (DLC exposure).
        """
        cell = self.vehicle.cell
        current_speed = self.vehicle.speed
        lc = self.lane_change
        for side, direction in ((cell.left, Direction.LEFT), (cell.right, Direction.RIGHT)):
            if side and side.find_blockage(self.blockage_scan) is None:
                side_leader = side.find_leader(self.look_ahead)
                side_speed = side_leader.speed if side_leader else self._v_max
                p = probability_over(
                    dlc_probability(side_speed, current_speed, lc.dlc_k, lc.dlc_v0), elapsed)
                if self.streams.dlc.random() < p:
                    return direction
        return Direction.FORWARD

    def _lane_changes_to_destination(self) -> int:
        """Number of lane changes needed to reach destination lane."""
        vehicle = self.vehicle
        if (vehicle.cell is None or vehicle.destination_cell_idx is None
                or vehicle.destination_lane is None):
            return 0
        return abs(vehicle.cell.lane.idx - vehicle.destination_lane)

    def _remaining_distance_ratio(self) -> float:
        """Fraction of trip remaining (1.0 at origin, 0.0 at destination)."""
        vehicle = self.vehicle
        if (
            vehicle.cell is None
            or vehicle.destination_cell_idx is None
            or vehicle.initial_distance is None
            or vehicle.initial_distance <= 0
        ):
            return 1.0
        leg_length = vehicle.destination_cell_idx - vehicle.route_start_idx
        if leg_length <= 0:
            return 1.0
        remaining = max(0, vehicle.destination_cell_idx - vehicle.cell.idx)
        return min(1.0, remaining / leg_length)

    def _direction_toward_destination(self) -> Direction:
        """Which direction to go to approach destination lane."""
        vehicle = self.vehicle
        if vehicle.cell is None or vehicle.destination_lane is None:
            return Direction.FORWARD
        current_lane = vehicle.cell.lane.idx
        if vehicle.destination_lane < current_lane:
            return Direction.RIGHT
        if vehicle.destination_lane > current_lane:
            return Direction.LEFT
        return Direction.FORWARD

    def _direction_away_from_blockage(self) -> Direction:
        """Pick a direction to escape a blocked lane.

        Prefer a neighbouring lane that is open; right first (toward slower lanes,
        conventional merging); if both are blocked, any lane that exists.
        """
        cell = self.vehicle.cell
        if cell is None:
            return Direction.FORWARD
        has_right = cell.right is not None
        has_left = cell.left is not None
        if has_right and cell.right.find_blockage(self.look_ahead) is None:
            return Direction.RIGHT
        if has_left and cell.left.find_blockage(self.look_ahead) is None:
            return Direction.LEFT
        if has_right:
            return Direction.RIGHT
        if has_left:
            return Direction.LEFT
        return Direction.FORWARD


class HumanDriver(Driver):
    """A human: decides every action interval in its own process, sooner when woken."""

    kind = "human"

    def __init__(self, cfg: HumanDriverConfig, streams: DriverStreams, traits: DriverTraits):
        """A human driver with its own sampled traits.

        Args:
            cfg: the population config.
            streams: the shared decision streams.
            traits: this driver's values (`TraitSampler.draw`).
        """
        super().__init__(cfg, streams, traits)
        self._process: Optional[simpy.Process] = None
        self._wake_event: Optional[simpy.Event] = None
        self._last_eval_time: float = -999.0

    def start(self):
        """Start deciding."""
        self._process = self.env.process(self._run())

    def _run(self):
        """Decide, then wait for the action interval or a wake-up, whichever comes first.

        Drivers are reactive in congestion (neighbours move often) and relaxed in free flow
        (the timeout dominates).
        """
        while self.vehicle.active:
            self._wake_event = self.env.event()
            self._last_eval_time = self.env.now
            self.decide()
            yield self.env.timeout(self.action_interval) | self._wake_event

    def wake(self):
        """Decide now, unless this driver decided within `min_reeval_ratio` of tau."""
        if self._wake_event is None or self._wake_event.triggered:
            return
        if self.env.now - self._last_eval_time < self.tau * self.cfg.min_reeval_ratio:
            return
        self._wake_event.succeed()



class AutonomousDriver(Driver):
    """An autonomous driver: its controller decides for it every controller interval."""

    kind = "autonomous"

    def __init__(self, cfg: AutonomousDriverConfig, streams: DriverStreams,
                 controller: AutonomousController):
        """An autonomous driver, registered with `controller`.

        A blocked vehicle retries its move at the controller rate, not at the action interval
        of the config (D-2026-09-19-19).

        Args:
            cfg: the driver config (exact values).
            streams: the shared decision streams.
            controller: the controller that decides for it.
        """
        super().__init__(cfg, streams)
        self.action_interval = controller.cfg.dt
        controller.register(self)
