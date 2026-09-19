"""Cell: the fundamental spatial unit of the ODCA-DES framework (D-2026-09-19-35).

Each cell is a SimPy PriorityResource with capacity 1, meaning at most one
vehicle can occupy it at a time. Cells form a linked list within a lane
(next/previous) and have lateral references to adjacent lanes (left/right).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

import simpy

if TYPE_CHECKING:
    from odca.infrastructure.lane import Lane


class Cell:
    """One cell: a capacity-1 resource, its occupant, its neighbours and its speed limit.

    The neighbour links (`next`, `previous`, `left`, `right` and the four diagonals) are plain
    attributes, set when the lanes are built and linked (`Lane`, `Freeway.link_neighbours`).
    """

    __slots__ = (
        "idx", "lane", "resource", "next", "previous", "left", "right",
        "left_next", "left_prev", "right_next", "right_prev",
        "vehicle", "_blocked", "speed_limit", "exits", "entry",
    )

    def __init__(self, idx: int, env: simpy.Environment,
                 speed_limit: float = float("inf")):
        """An empty, open cell with no links yet.

        Args:
            idx: position along the lane.
            env: the SimPy environment of its resource.
            speed_limit: cells/s.
        """
        self.idx = idx
        self.lane: Optional[Lane] = None
        self.resource = simpy.PriorityResource(env, capacity=1)
        self.next: Optional[Cell] = None
        self.previous: Optional[Cell] = None
        self.left: Optional[Cell] = None         # same index, lane to the left
        self.right: Optional[Cell] = None        # same index, lane to the right
        self.left_next: Optional[Cell] = None    # diagonals
        self.left_prev: Optional[Cell] = None
        self.right_next: Optional[Cell] = None
        self.right_prev: Optional[Cell] = None
        self.vehicle = None  # the vehicle whose position this cell is
        self._blocked: bool = False
        self.speed_limit: float = speed_limit  # cell-level speed limit (cells/s)
        self.exits: list = []  # DestinationCells a vehicle leaves into from here (set by Freeway)
        self.entry = None  # the OriginCell vehicles come in through, if any (set by Freeway)

    # --- Occupancy ---

    @property
    def is_occupied(self) -> bool:
        """Whether a vehicle holds the cell's lock."""
        return len(self.resource.users) > 0

    @property
    def blocked(self) -> bool:
        """Whether the cell is closed to vehicles."""
        return self._blocked

    @blocked.setter
    def blocked(self, value: bool):
        """Open or close the cell, keeping its lane's count of closed cells.

        Args:
            value: closed.
        """
        value = bool(value)
        if value != self._blocked and self.lane is not None:
            self.lane.blocked_count += 1 if value else -1
        self._blocked = value

    # --- Leader / follower detection ---

    def find_leader(self, look_ahead: int):
        """The nearest vehicle ahead within `look_ahead` cells, or None.

        Args:
            look_ahead: cells to scan.
        """
        cell = self
        for _ in range(look_ahead):
            cell = cell.next
            if cell is None:
                return None
            if cell.vehicle is not None:
                return cell.vehicle
        return None

    def find_follower(self, look_behind: int):
        """The nearest vehicle behind within `look_behind` cells, or None.

        Args:
            look_behind: cells to scan.
        """
        cell = self
        for _ in range(look_behind):
            cell = cell.previous
            if cell is None:
                return None
            if cell.vehicle is not None:
                return cell.vehicle
        return None

    def find_blockage(self, look_ahead: int) -> Optional[int]:
        """Distance to the nearest closed cell ahead within `look_ahead` cells, or None.

        A lane with no closed cell answers at once (`Lane.blocked_count`).

        Args:
            look_ahead: cells to scan.
        """
        lane = self.lane
        if lane is not None and not lane.blocked_count:
            return None
        cell = self
        for d in range(1, look_ahead + 1):
            cell = cell.next
            if cell is None:
                return None
            if cell._blocked:
                return d
        return None

    def __repr__(self):
        lane_id = self.lane.idx if self.lane else "?"
        occ = "B" if self._blocked else ""
        return f"Cell(L{lane_id}, {self.idx}{occ})"


class EndpointCell(Cell):
    """A cell off the road where trips start or end, joined to one road cell (D-2026-09-19-27).

    With no speed limit it is transparent: vehicles pass it at no time and it holds no lock,
    so trips run exactly as without it. With a speed limit it is a real cell: a vehicle takes
    1 / limit seconds to pass it and holds it for tau more, so at most
    3600 / (tau + 1 / limit) veh/h get through: a metered on-ramp or a throttled exit.
    """

    __slots__ = ("name", "road_cell")

    def __init__(self, name: str, road_cell: Cell, env: simpy.Environment):
        """An unlimited endpoint joined to `road_cell`.

        Args:
            name: the origin or destination it belongs to.
            road_cell: the road cell it joins.
            env: the SimPy environment.
        """
        super().__init__(idx=road_cell.idx, env=env)
        self.name = name
        self.road_cell = road_cell

    @property
    def limited(self) -> bool:
        """Whether a speed limit makes it a real cell."""
        return self.speed_limit != float("inf")


class OriginCell(EndpointCell):
    """Where vehicles of one origin wait and enter the road cell it joins."""


class DestinationCell(EndpointCell):
    """Where vehicles of one destination leave the road, from the road cell it joins."""

    __slots__ = ("destination",)

    def __init__(self, name: str, road_cell: Cell, env: simpy.Environment, destination):
        """An unlimited exit of `destination` from `road_cell`.

        Args:
            name: the destination's name.
            road_cell: the last road cell before the exit.
            env: the SimPy environment.
            destination: the `Destination` it belongs to.
        """
        super().__init__(name, road_cell, env)
        self.destination = destination
