"""Freeway: a multi-lane segment with on-ramps and off-ramps."""

from __future__ import annotations

from typing import Dict, List, Set

import simpy

from odca.infrastructure.lane import Lane


class Freeway:
    def __init__(
        self,
        env: simpy.Environment,
        num_lanes: int,
        num_cells: int,
        speed_limit: float,
        onramp_cells: List[int],
        offramp_cells: List[int],
    ):
        self.env = env
        self.num_lanes = num_lanes
        self.num_cells = num_cells
        self.speed_limit = speed_limit
        self.onramp_cells: Set[int] = set(onramp_cells)
        self.offramp_cells: Set[int] = set(offramp_cells)

        # Build lanes (1 = rightmost, num_lanes = leftmost)
        self.lanes: List[Lane] = []
        for i in range(num_lanes):
            lane = Lane(idx=i + 1, num_cells=num_cells, env=env,
                        speed_limit=speed_limit)
            lane.freeway = self
            self.lanes.append(lane)

        # Wire lateral references
        for i in range(num_lanes):
            if i > 0:
                self.lanes[i].right = self.lanes[i - 1]
            if i < num_lanes - 1:
                self.lanes[i].left = self.lanes[i + 1]

        # Quick lookup by lane index (1-based)
        self._lane_by_idx: Dict[int, Lane] = {l.idx: l for l in self.lanes}

    def lane(self, idx: int) -> Lane:
        """Get lane by 1-based index."""
        return self._lane_by_idx[idx]

    @property
    def rightmost(self) -> Lane:
        return self.lanes[0]

    @property
    def leftmost(self) -> Lane:
        return self.lanes[-1]

    def cell(self, lane_idx: int, cell_idx: int):
        """Get a specific cell."""
        return self._lane_by_idx[lane_idx].cells[cell_idx]

    def block_cells(self, lane_idx: int, start_cell: int, end_cell: int):
        """Block a range of cells in a lane (inclusive).

        Used for lane drops, incidents, or work zones. Blocked cells
        cannot be acquired by vehicles, forcing lane changes upstream.
        """
        lane = self._lane_by_idx[lane_idx]
        for i in range(start_cell, min(end_cell + 1, len(lane.cells))):
            lane.cells[i].blocked = True

    def unblock_cells(self, lane_idx: int, start_cell: int, end_cell: int):
        """Unblock a range of cells in a lane (inclusive)."""
        lane = self._lane_by_idx[lane_idx]
        for i in range(start_cell, min(end_cell + 1, len(lane.cells))):
            lane.cells[i].blocked = False

    def set_speed_limit(self, speed_limit: float, lane_idx: int = 0,
                        start_cell: int = 0, end_cell: int = -1):
        """Set speed limit on a range of cells.

        Args:
            speed_limit: Speed limit in cells/s.
            lane_idx: Lane to apply to (1-based). 0 = all lanes.
            start_cell: First cell (inclusive).
            end_cell: Last cell (inclusive). -1 = last cell in lane.
        """
        lanes = self.lanes if lane_idx == 0 else [self._lane_by_idx[lane_idx]]
        for lane in lanes:
            end = end_cell if end_cell >= 0 else len(lane.cells) - 1
            for i in range(start_cell, min(end + 1, len(lane.cells))):
                lane.cells[i].speed_limit = speed_limit

    def __repr__(self):
        return f"Freeway(lanes={self.num_lanes}, cells={self.num_cells})"
