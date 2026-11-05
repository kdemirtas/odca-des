"""Platoon: a train of autonomous vehicles in one lane (D-2026-11-05-1).

The members are ordered front first. The leader, at the front, decides for the platoon: its
speed by car following against the traffic ahead, and any lane change. The followers drive at
the leader's speed and change lanes only together with it. Every member but the tail releases a
cell the moment it takes the next one, so there is no headway inside the train; the tail keeps
its own tau, which is the headway the traffic behind sees. A platoon of m vehicles therefore
passes a point in m l / v + tau seconds, the cycle of the train-platoon capacity formula.

A platoon exists only with two members or more: a removal or split that leaves one vehicle
dissolves it, and that vehicle drives solo again.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional, Set

from odca.entity.vehicle import Direction

if TYPE_CHECKING:
    from odca.entity.vehicle import Vehicle
    from odca.infrastructure.cell import Cell


class Platoon:
    """Two or more autonomous vehicles in one lane moving as one train, front first."""

    def __init__(self, platoon_id: int, members: List[Vehicle]):
        """A platoon of `members`, front first; each member's driver is told it belongs here.

        Args:
            platoon_id: its number within the run, given by the controller.
            members: two or more vehicles driven by `PlatoonDriver`s, front first.

        Raises:
            ValueError: fewer than two members.
        """
        if len(members) < 2:
            raise ValueError(f"a platoon needs two members or more, got {len(members)}")
        self.id = platoon_id
        self._members: List[Vehicle] = list(members)
        # destination cells already separated from this platoon's line by a destination split
        self.split_destinations: Set[int] = set()
        for member in self._members:
            member.driver.platoon = self

    # ------------------------------------------------------------------
    # State
    # ------------------------------------------------------------------

    @property
    def members(self) -> List[Vehicle]:
        """The members, front first (a copy)."""
        return list(self._members)

    @property
    def leader(self) -> Vehicle:
        """The front member, which decides for the platoon."""
        return self._members[0]

    @property
    def tail(self) -> Vehicle:
        """The rear member, the only one that keeps its tau."""
        return self._members[-1]

    @property
    def size(self) -> int:
        """How many vehicles it holds."""
        return len(self._members)

    @property
    def active(self) -> bool:
        """Whether it still exists (two members or more)."""
        return len(self._members) >= 2

    def lane_idx(self) -> Optional[int]:
        """The leader's lane, or None once the leader has left the road."""
        cell = self.leader.cell
        return cell.lane.idx if cell is not None else None

    # ------------------------------------------------------------------
    # Formation operations
    # ------------------------------------------------------------------

    def remove(self, vehicle: Vehicle) -> Optional[List[Vehicle]]:
        """Take `vehicle` out; it drives solo again.

        Removing the leader makes the next member the leader; removing a middle member cuts
        the platoon in two, and the rear part is returned for the controller to form anew.
        Whatever is left with one vehicle is dissolved.

        Args:
            vehicle: a member.

        Returns:
            The members behind `vehicle` when it was a middle member and two or more are left
            behind it, front first; else None.
        """
        idx = self._members.index(vehicle)
        self._members.pop(idx)
        vehicle.driver.platoon = None
        behind = None
        if 0 < idx < len(self._members):
            behind = self._members[idx:]
            self._members = self._members[:idx]
            if len(behind) < 2:
                behind[0].driver.platoon = None
                behind = None
        if len(self._members) < 2:
            self.dissolve()
        return behind

    def split_at(self, idx: int) -> List[Vehicle]:
        """Cut the platoon behind member `idx - 1`; members `idx` on drive solo again.

        Args:
            idx: the first member to leave, 1 to size - 1.

        Returns:
            The members that left, front first.
        """
        back = self._members[idx:]
        self._members = self._members[:idx]
        for member in back:
            member.driver.platoon = None
        if len(self._members) < 2:
            self.dissolve()
        return back

    def merge(self, behind: Platoon):
        """Append the platoon `behind` to this one's tail; `behind` is dissolved into it.

        Args:
            behind: an active platoon just behind this one in the same lane.
        """
        joining = behind._members
        behind._members = []
        self.split_destinations |= behind.split_destinations
        for member in joining:
            member.driver.platoon = self
        self._members.extend(joining)

    def dissolve(self):
        """Every member drives solo again."""
        for member in self._members:
            member.driver.platoon = None
        self._members = []

    # ------------------------------------------------------------------
    # Lane change as contiguous gap acceptance
    # ------------------------------------------------------------------

    def target_cells(self, direction: Direction) -> Optional[List[Cell]]:
        """The cells the train would move into by changing lanes toward `direction`.

        From the cell beside-and-ahead of the tail to the one beside-and-ahead of the leader,
        in the target lane: the m contiguous cells of a platoon lane change, plus any gap
        between members. None when a member is not in the leader's lane or the target lane
        does not reach.

        Args:
            direction: LEFT or RIGHT.
        """
        lead_cell, tail_cell = self.leader.cell, self.tail.cell
        if lead_cell is None or tail_cell is None:
            return None
        lane = lead_cell.lane
        if any(m.cell is None or m.cell.lane is not lane for m in self._members):
            return None
        lead_target = lead_cell.left_next if direction is Direction.LEFT else lead_cell.right_next
        if lead_target is None:
            return None
        cells = lead_target.lane.cells
        first, last = tail_cell.idx + 1, lead_target.idx
        if first > last or last >= len(cells):
            return None
        return cells[first:last + 1]

    def target_lane_free(self, direction: Direction) -> bool:
        """Whether every cell of `target_cells(direction)` is open, empty and unlocked.

        Args:
            direction: LEFT or RIGHT.
        """
        cells = self.target_cells(direction)
        return cells is not None and all(
            not c.blocked and c.vehicle is None and not c.is_occupied for c in cells)

    def __repr__(self):
        lead = self.leader.id if self._members else "?"
        return f"Platoon(id={self.id}, size={self.size}, leader={lead})"
