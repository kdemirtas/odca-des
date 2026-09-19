"""Cell: the fundamental spatial unit of the ODCA-DES framework.

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
    __slots__ = (
        "idx", "lane", "resource",
        "_next", "_prev", "_vehicle", "_blocked",
        "speed_limit", "exits", "entry",
    )

    def __init__(self, idx: int, env: simpy.Environment,
                 speed_limit: float = float("inf")):
        self.idx = idx
        self.lane: Optional[Lane] = None
        self.resource = simpy.PriorityResource(env, capacity=1)
        self._next: Optional[Cell] = None
        self._prev: Optional[Cell] = None
        self._vehicle = None  # currently registered vehicle
        self._blocked: bool = False
        self.speed_limit: float = speed_limit  # cell-level speed limit (cells/s)
        self.exits: list = []  # DestinationCells a vehicle leaves into from here (set by Freeway)
        self.entry = None  # the OriginCell vehicles come in through, if any (set by Freeway)

    # --- Linked-list navigation ---

    @property
    def next(self) -> Optional[Cell]:
        return self._next

    @property
    def previous(self) -> Optional[Cell]:
        return self._prev

    @property
    def left(self) -> Optional[Cell]:
        """Cell at same index in the left (higher-index) lane."""
        if self.lane and self.lane.left:
            return self.lane.left.cells[self.idx]
        return None

    @property
    def right(self) -> Optional[Cell]:
        """Cell at same index in the right (lower-index) lane."""
        if self.lane and self.lane.right:
            return self.lane.right.cells[self.idx]
        return None

    @property
    def left_next(self) -> Optional[Cell]:
        """Diagonal forward-left cell."""
        left = self.left
        return left.next if left and left.next else None

    @property
    def left_prev(self) -> Optional[Cell]:
        """Diagonal backward-left cell."""
        left = self.left
        return left.previous if left and left.previous else None

    @property
    def right_next(self) -> Optional[Cell]:
        """Diagonal forward-right cell."""
        right = self.right
        return right.next if right and right.next else None

    @property
    def right_prev(self) -> Optional[Cell]:
        """Diagonal backward-right cell."""
        right = self.right
        return right.previous if right and right.previous else None

    # --- Occupancy ---

    @property
    def vehicle(self):
        return self._vehicle

    @vehicle.setter
    def vehicle(self, v):
        self._vehicle = v

    @property
    def is_occupied(self) -> bool:
        return len(self.resource.users) > 0

    @property
    def blocked(self) -> bool:
        return self._blocked

    @blocked.setter
    def blocked(self, value: bool):
        self._blocked = value

    # --- Leader / follower detection ---

    def find_leader(self, look_ahead: int):
        """Scan forward up to look_ahead cells for an occupying vehicle."""
        cell = self
        for _ in range(look_ahead):
            cell = cell._next
            if cell is None:
                return None
            if cell._vehicle is not None:
                return cell._vehicle
        return None

    def find_follower(self, look_behind: int):
        """Scan backward up to look_behind cells for an occupying vehicle."""
        cell = self
        for _ in range(look_behind):
            cell = cell._prev
            if cell is None:
                return None
            if cell._vehicle is not None:
                return cell._vehicle
        return None

    def find_blockage(self, look_ahead: int) -> Optional[int]:
        """Scan forward for a blocked cell. Returns distance if found, None otherwise."""
        cell = self
        for d in range(1, look_ahead + 1):
            cell = cell._next
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
