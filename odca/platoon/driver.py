"""PlatoonDriver: an autonomous driver that can be a platoon member (D-2026-11-05-1).

Solo, it decides exactly as `AutonomousDriver`. As the leader of a platoon it decides as a solo
driver too, but no member changes lanes alone: with `train_lane_changes` off (the default) a
lane change the leader draws is refused, and with it on the change happens only for the whole
train, when the target lane is free over the train's length (D-2026-11-05-4). A member that has
to reach another lane leaves the platoon first (the controller's split phase). As a follower it takes the leader's speed, closing up on the member ahead until the train is
contiguous, and keeps to the leader's lane, with no direction decision of its own. Every member but the tail releases a cell at once (`release_tau` 0).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional, Tuple

from odca.entity.driver import AutonomousDriver
from odca.entity.vehicle import Direction, LaneChangeReason

if TYPE_CHECKING:
    from odca.entity.vehicle import Vehicle
    from odca.platoon.controller import PlatoonController
    from odca.platoon.platoon import Platoon


# a spacing excess (cells beyond the jam spacing) up to this counts as closed up
CONTIGUOUS_TOLERANCE = 0.5


class PlatoonDriver(AutonomousDriver):
    """An autonomous driver that drives solo or as a platoon leader or follower."""

    def __init__(self, cfg, streams, controller: PlatoonController):
        """A driver registered with the platoon controller, solo until it is grouped.

        Args:
            cfg: the autonomous driver config.
            streams: the shared decision streams.
            controller: the platoon controller.
        """
        super().__init__(cfg, streams, controller)
        self.controller = controller
        self._platoon: Optional[Platoon] = None
        # (time, platoon id or None) at every change of membership, for the section counts
        self.membership: List[Tuple[float, Optional[int]]] = []

    @property
    def platoon(self) -> Optional[Platoon]:
        """The platoon this driver's vehicle is in, or None when solo."""
        return self._platoon

    @platoon.setter
    def platoon(self, platoon: Optional[Platoon]):
        """Join `platoon` (None: drive solo), logging the change.

        Args:
            platoon: the new platoon, or None.
        """
        new_id = None if platoon is None else platoon.id
        old_id = None if self._platoon is None else self._platoon.id
        self._platoon = platoon
        if new_id != old_id:
            self.membership.append((self.env.now if self.env else 0.0, new_id))

    def platoon_id_at(self, time: float) -> Optional[int]:
        """The id of the platoon the vehicle was in at `time`, or None when solo then.

        Args:
            time: a simulation time.
        """
        current = None
        for changed, platoon_id in self.membership:
            if changed > time:
                break
            current = platoon_id
        return current

    @property
    def is_follower(self) -> bool:
        """Whether this driver follows a platoon leader."""
        return self.platoon is not None and self.platoon.leader is not self.vehicle

    @property
    def is_leader(self) -> bool:
        """Whether this driver leads a platoon."""
        return self.platoon is not None and self.platoon.leader is self.vehicle

    @property
    def release_tau(self) -> float:
        """0 for a platoon member that is not the tail, else tau."""
        if self.platoon is not None and self.platoon.tail is not self.vehicle:
            return 0.0
        return self.tau

    def _moving_leader(self) -> Optional[Vehicle]:
        """The platoon leader when this driver follows one that is on the road and moving."""
        if not self.is_follower:
            return None
        leader = self.platoon.leader
        if not leader.active or leader.speed <= 0:
            return None
        return leader

    def evaluate_speed(self):
        """A follower drives at its leader's speed and closes up on the member ahead; a leader
        whose train has a gap eases off so the followers can close it.

        The speed is the leader's plus the spacing to the member directly ahead beyond the jam
        spacing (Newell's rule with tau 0): a member formed a few cells behind closes the gap,
        and an adjacent one drives at exactly the leader's speed, so the train becomes and
        stays contiguous. Anyone else, and a follower whose leader has stopped or left, decides
        as a solo driver.
        """
        leader = self._moving_leader()
        if leader is None:
            super().evaluate_speed()
            if self.is_leader:
                self._ease_off_for_gaps()
            return
        vehicle = self.vehicle
        self.count_speed_evaluations += 1
        members = self.platoon.members
        ahead = members[members.index(vehicle) - 1]
        spacing = ahead.fractional_position - vehicle.fractional_position
        speed = min(leader.speed + max(0.0, spacing - self._d), vehicle.effective_v_max())
        vehicle.set_target_speed(speed)

    def _ease_off_for_gaps(self):
        """A leader whose train still has a gap drives up to `formation_speed_diff` below its
        free-flow speed, so the followers, which may drive at it, close up."""
        members = self.platoon.members
        excess = max(ahead.fractional_position - behind.fractional_position - self._d
                     for ahead, behind in zip(members, members[1:]))
        if excess <= CONTIGUOUS_TOLERANCE:
            return
        vehicle = self.vehicle
        closing = min(excess, self.controller.platoon_cfg.formation_speed_diff)
        cap = max(0.0, vehicle.effective_v_max() - closing)
        if vehicle.speed > cap:
            vehicle.set_target_speed(cap)

    def evaluate_direction(self):
        """A follower keeps to its leader's lane; a leader changes lanes only with the train,
        and only with `train_lane_changes` on (D-2026-11-05-4); off, a leader's lane change
        is refused and the platoon stays in its lane.

        A follower in the leader's lane asks for what the leader asked for; one left behind in
        another lane asks to move toward the leader's lane, for the reason of the leader's last
        lane change. A follower's exposure clock still runs, so a vehicle leaving the platoon
        does not carry the time it spent in it into its first own lane-change draw.
        """
        vehicle = self.vehicle
        if vehicle.cell is None:
            return
        if self.is_follower:
            self._direction_exposure()
            self._follow_leader_direction()
            return
        super().evaluate_direction()
        direction = vehicle.desired_direction
        if not self.is_leader or direction is Direction.FORWARD:
            return
        size = self.platoon.size
        if self.controller.platoon_cfg.train_lane_changes:
            self.controller.train_lc_attempts[size] += 1
        if self.controller.platoon_cfg.train_lane_changes and self.platoon.target_lane_free(
                direction):
            self.controller.count_train_lc_requests += 1
            self.controller.train_lc_granted[size] += 1
        else:
            vehicle.request_direction(Direction.FORWARD)
            self.controller.count_train_lc_refusals += 1
        for member in self.platoon.members[1:]:
            member.driver._follow_leader_direction()

    def _follow_leader_direction(self):
        """Ask for the leader's direction, or for the way to the leader's lane."""
        vehicle, leader = self.vehicle, self.platoon.leader
        if leader.cell is None or vehicle.cell is None:
            vehicle.request_direction(Direction.FORWARD)
            return
        own_lane, leader_lane = vehicle.cell.lane.idx, leader.cell.lane.idx
        if own_lane == leader_lane:
            vehicle.request_direction(leader.desired_direction, leader.direction_reason)
            return
        direction = Direction.LEFT if leader_lane > own_lane else Direction.RIGHT
        reason = (leader.lane_changes[-1].reason if leader.lane_changes
                  else LaneChangeReason.MLC_DESTINATION)
        vehicle.request_direction(direction, reason)
