"""Gipps lane-changing model (Gipps 1986), as a decision tree.

  1. Feasibility: is there a safe gap?
  2. Necessity: does the vehicle need to change lanes (mandatory)?
  3. Desirability: would a lane change improve speed (discretionary)?

Safety is a deceleration threshold for the new follower, given in m/s^2 in the config and
converted to cells/s^2 here (paper-lc-logistic:D-2026-10-03-11).
"""

from dataclasses import dataclass
from typing import Optional

from odca.entity.driver import HumanDriver
from odca.entity.vehicle import Direction, LaneChangeReason
from odca.params import CELL_LENGTH_M, BaseLaneChangeConfig, family_member

from models.neighbours import NeighbourState, observe


@family_member("gipps")
@dataclass(frozen=True, slots=True, kw_only=True)
class GippsLaneChangeConfig(BaseLaneChangeConfig):
    """The thresholds of the Gipps decision tree."""

    model: str = "gipps"
    b_safe: float = 4.0            # largest braking imposed on the new follower (m/s^2)
    min_gap: float = 1.0           # smallest acceptable gap, front or rear (cells)
    mlc_urgency_r0: float = 0.3    # a mandatory change is necessary once r <= r0 * n
    speed_threshold: float = 1.0   # speed advantage that makes a change desirable (cells/s)


def gipps_feasible(v: float, target: NeighbourState, cfg: GippsLaneChangeConfig) -> bool:
    """Whether the gap in the target lane is safe.

    Args:
        v: speed of the deciding vehicle (cells/s).
        target: the lane it would move to.
        cfg: the Gipps thresholds.
    """
    if target.has_leader and target.gap_front < cfg.min_gap:
        return False
    if target.has_follower:
        if target.gap_rear < cfg.min_gap:
            return False
        closing = target.v_follower - v
        # braking the follower needs to match speeds within the gap: closing^2 / (2 gap)
        needed_braking = closing ** 2 / (2 * max(target.gap_rear, 0.1))
        if closing > 0 and needed_braking > cfg.b_safe / CELL_LENGTH_M:
            return False
    return True


def gipps_necessary(remaining_ratio: float, needed: int, cfg: GippsLaneChangeConfig) -> bool:
    """Whether a mandatory lane change is due.

    Args:
        remaining_ratio: share of the trip remaining, 0 to 1.
        needed: lane changes still needed toward this side.
        cfg: the Gipps thresholds.
    """
    return needed > 0 and remaining_ratio <= min(1.0, cfg.mlc_urgency_r0 * needed)


def gipps_decision(v: float, target: NeighbourState, remaining_ratio: float, needed: int,
                   cfg: GippsLaneChangeConfig) -> Optional[LaneChangeReason]:
    """The Gipps decision for one side: the reason to change, or None to stay.

    Args:
        v: speed of the deciding vehicle (cells/s).
        target: the lane it would move to.
        remaining_ratio: share of the trip remaining, 0 to 1.
        needed: lane changes still needed toward this side (0 for the other side).
        cfg: the Gipps thresholds.
    """
    if not gipps_feasible(v, target, cfg):
        return None
    if gipps_necessary(remaining_ratio, needed, cfg):
        return LaneChangeReason.MLC_DESTINATION
    if target.lane_speed - v > cfg.speed_threshold:
        return LaneChangeReason.DLC
    return None


class GippsDriver(HumanDriver):
    """A human driver whose lane changes follow the Gipps decision tree."""

    lane_change_config = GippsLaneChangeConfig

    def evaluate_direction(self):
        """Choose the direction: a necessary change first, else a desirable one."""
        vehicle = self.vehicle
        cell = vehicle.cell
        if cell is None:
            return
        lc = self.lane_change
        # discretionary changes are off inside the cooldown, or altogether
        no_dlc = not lc.dlc_enabled or self.env.now - vehicle.last_lc_time < lc.dlc_cooldown
        needed = self._lane_changes_to_destination()
        remaining = self._remaining_distance_ratio()
        toward = self._direction_toward_destination()

        chosen, reason = Direction.FORWARD, None
        for side, direction in ((cell.left, Direction.LEFT), (cell.right, Direction.RIGHT)):
            if side is None:
                continue
            decision = gipps_decision(vehicle.speed, observe(side, self), remaining,
                                      needed if direction is toward else 0, lc)
            if decision is LaneChangeReason.MLC_DESTINATION:
                chosen, reason = direction, decision
                break
            if decision is LaneChangeReason.DLC and not no_dlc:
                chosen, reason = direction, decision
        vehicle.request_direction(chosen, reason)
