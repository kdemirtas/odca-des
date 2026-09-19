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
        """Join the last cell to the first: a ring road. Relinks the freeway's neighbours."""
        self.cells[-1].next = self.cells[0]
        self.cells[0].previous = self.cells[-1]
        if self.freeway is not None:
            self.freeway.link_neighbours()

    def __repr__(self):
        return f"Lane({self.idx}, cells={self.num_cells})"
