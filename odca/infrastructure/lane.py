"""Lane: an ordered sequence of cells representing one freeway lane."""

from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional

import simpy

from odca.infrastructure.cell import Cell

if TYPE_CHECKING:
    from odca.infrastructure.freeway import Freeway


class Lane:
    """A lane: its cells in order, its neighbours, and how many of its cells are closed."""

    def __init__(self, idx: int, num_cells: int, env: simpy.Environment,
                 speed_limit: float = float("inf")):
        """A lane of `num_cells` open cells linked front to back.

        Args:
            idx: 1 the rightmost.
            num_cells: cells in the lane.
            env: the SimPy environment of the cells.
            speed_limit: cells/s.
        """
        self.idx = idx
        self.blocked_count = 0  # closed cells; kept by Cell.blocked
        self.env = env
        self.freeway: Optional[Freeway] = None
        self.left: Optional[Lane] = None   # higher-index lane
        self.right: Optional[Lane] = None  # lower-index lane

        # Create cells and wire the linked list
        self.cells: List[Cell] = []
        for c in range(num_cells):
            cell = Cell(idx=c, env=env, speed_limit=speed_limit)
            cell.lane = self
            if self.cells:
                cell.previous = self.cells[-1]
                self.cells[-1].next = cell
            self.cells.append(cell)

    @property
    def num_cells(self) -> int:
        return len(self.cells)

    @property
    def first(self) -> Cell:
        return self.cells[0]

    @property
    def last(self) -> Cell:
        return self.cells[-1]

    def make_periodic(self):
        """Join the last cell to the first. Relinks the freeway's neighbours.

        Only the links change: distances and exits stay those of an open road. A ring road
        with exits is `NetworkConfig.ring` (D-2026-11-08-1).
        """
        self.cells[-1].next = self.cells[0]
        self.cells[0].previous = self.cells[-1]
        if self.freeway is not None:
            self.freeway.link_neighbours()

    @property
    def ring(self) -> bool:
        """Whether this lane is part of a ring road (`NetworkConfig.ring`, D-2026-11-08-1)."""
        return self.freeway is not None and self.freeway.ring

    def cells_ahead(self, from_idx: int, to_idx: int) -> int:
        """Cells from cell `from_idx` forward to cell `to_idx`: `to_idx - from_idx`, negative
        when `to_idx` lies behind; on a ring, taken forward around the ring, 0 to
        num_cells - 1 (D-2026-11-08-1).

        Args:
            from_idx: the cell counted from.
            to_idx: the cell counted to.
        """
        if self.ring:
            return (to_idx - from_idx) % self.num_cells
        return to_idx - from_idx

    def spacing(self, behind_idx: int, ahead_idx: int) -> int:
        """Cells from a vehicle at `behind_idx` to one at `ahead_idx`: their index difference
        in size on an open road, taken forward around the ring on a ring (D-2026-11-08-1).

        Args:
            behind_idx: the rear vehicle's cell.
            ahead_idx: the front vehicle's cell.
        """
        if self.ring:
            return (ahead_idx - behind_idx) % self.num_cells
        return abs(ahead_idx - behind_idx)

    def __repr__(self):
        return f"Lane({self.idx}, cells={self.num_cells})"
