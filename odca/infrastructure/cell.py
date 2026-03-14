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
        "speed_limit",
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
