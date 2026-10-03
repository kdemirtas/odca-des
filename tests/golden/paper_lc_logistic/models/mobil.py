"""MOBIL lane-changing model (Kesting, Treiber, Helbing 2007) on IDM accelerations.

Minimizing Overall Braking Induced by Lane changes.

Safety criterion:
    acc'(new_follower) > -b_safe

Incentive criterion:
    acc'(subject_new) - acc(subject_old)
        > p * [acc(new_follower_old) - acc'(new_follower_new)] + a_thr

where primed quantities denote post-lane-change values. Accelerations are given in m/s^2 in
the config, as in the literature and the manuscript, and converted to cells/s^2 here
(paper-lc-logistic:D-2026-10-03-11).
"""

import math
from dataclasses import dataclass
from typing import Optional

from odca.entity.driver import HumanDriver
from odca.entity.vehicle import Direction, LaneChangeReason
from odca.params import CELL_LENGTH_M, BaseLaneChangeConfig, family_member

from models.neighbours import NeighbourState, observe


@family_member("mobil")
@dataclass(frozen=True, slots=True, kw_only=True)
class MobilLaneChangeConfig(BaseLaneChangeConfig):
    """MOBIL with its IDM car-following parameters."""

    model: str = "mobil"
    politeness: float = 0.3
    b_safe: float = 4.0            # largest braking imposed on the new follower (m/s^2)
    a_threshold: float = 0.2       # incentive threshold (m/s^2)
    mlc_urgency_r0: float = 0.3    # a mandatory change is forced once r <= r0 * n
    idm_v0: float = 5.2            # desired speed (cells/s)
    idm_headway: float = 1.5       # desired time headway (s)
    idm_a: float = 1.0             # maximum acceleration (m/s^2)
    idm_b: float = 1.5             # comfortable deceleration (m/s^2)
    idm_s0: float = 1.0            # minimum gap (cells)
    idm_delta: float = 4.0         # acceleration exponent


def idm_free_acceleration(v: float, cfg: MobilLaneChangeConfig) -> float:
    """IDM acceleration with no leader (cells/s^2).

    Args:
        v: speed (cells/s).
        cfg: the IDM parameters.
    """
    return cfg.idm_a / CELL_LENGTH_M * (1 - (v / cfg.idm_v0) ** cfg.idm_delta)


def idm_acceleration(v: float, gap: float, v_leader: float,
                     cfg: MobilLaneChangeConfig) -> float:
    """IDM acceleration behind a leader (cells/s^2).

    Args:
        v: speed of the vehicle (cells/s).
        gap: gap to the leader (cells).
        v_leader: speed of the leader (cells/s).
        cfg: the IDM parameters.
    """
    a = cfg.idm_a / CELL_LENGTH_M
    b = cfg.idm_b / CELL_LENGTH_M
    if gap <= 0:
        return -b * 5  # emergency
    closing_term = v * (v - v_leader) / (2 * math.sqrt(a * b))
    s_star = cfg.idm_s0 + max(0.0, v * cfg.idm_headway + closing_term)
    return a * (1 - (v / cfg.idm_v0) ** cfg.idm_delta) - a * (s_star / gap) ** 2


def mobil_incentive(v: float, current: NeighbourState, target: NeighbourState,
                    cfg: MobilLaneChangeConfig) -> Optional[float]:
    """The MOBIL incentive of moving to the target lane (cells/s^2), or None if unsafe.

    Args:
        v: speed of the deciding vehicle (cells/s).
        current: its own lane.
        target: the lane it would move to.
        cfg: the MOBIL and IDM parameters.
    """
    if current.has_leader:
        acc_old = idm_acceleration(v, current.gap_front, current.v_leader, cfg)
    else:
        acc_old = idm_free_acceleration(v, cfg)
    if target.has_leader:
        acc_new = idm_acceleration(v, target.gap_front, target.v_leader, cfg)
    else:
        acc_new = idm_free_acceleration(v, cfg)

    disadvantage = 0.0
    if target.has_follower:
        follower_new = idm_acceleration(target.v_follower, target.gap_rear, v, cfg)
        if follower_new < -cfg.b_safe / CELL_LENGTH_M:
            return None
        if target.has_leader:
            # before the change the follower followed the target lane's leader
            follower_old = idm_acceleration(target.v_follower,
                                            target.gap_rear + target.gap_front,
                                            target.v_leader, cfg)
        else:
            follower_old = idm_free_acceleration(target.v_follower, cfg)
        disadvantage = follower_old - follower_new
    return acc_new - acc_old - cfg.politeness * disadvantage


class MobilDriver(HumanDriver):
    """A human driver whose lane changes follow MOBIL."""

    lane_change_config = MobilLaneChangeConfig

    def evaluate_direction(self):
        """Choose the direction: a forced mandatory change near the exit, else MOBIL.

        With `dlc_enabled` off, or inside the cooldown, only the forced change is made.
        """
        vehicle = self.vehicle
        cell = vehicle.cell
        if cell is None:
            return
        lc = self.lane_change
        needed = self._lane_changes_to_destination()
        if needed > 0 and self._remaining_distance_ratio() <= lc.mlc_urgency_r0 * needed:
            vehicle.request_direction(self._direction_toward_destination(),
                                      LaneChangeReason.MLC_DESTINATION)
            return
        if not lc.dlc_enabled or self.env.now - vehicle.last_lc_time < lc.dlc_cooldown:
            vehicle.request_direction(Direction.FORWARD)
            return

        current = observe(cell, self)
        best_direction, best = Direction.FORWARD, lc.a_threshold / CELL_LENGTH_M
        for side, direction in ((cell.left, Direction.LEFT), (cell.right, Direction.RIGHT)):
            if side is None:
                continue
            incentive = mobil_incentive(vehicle.speed, current, observe(side, self), lc)
            if incentive is not None and incentive > best:
                best_direction, best = direction, incentive
        if best_direction is Direction.FORWARD:
            vehicle.request_direction(Direction.FORWARD)
        elif needed > 0 and best_direction is self._direction_toward_destination():
            vehicle.request_direction(best_direction, LaneChangeReason.MLC_DESTINATION)
        else:
            vehicle.request_direction(best_direction, LaneChangeReason.DLC)
