"""Lane: an ordered sequence of cells representing one freeway lane."""

from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional

import simpy

from odca.infrastructure.cell import Cell

if TYPE_CHECKING:
    from odca.infrastructure.freeway import Freeway


class Lane:
    def __init__(self, idx: int, num_cells: int, env: simpy.Environment,
                 speed_limit: float = float("inf")):
        self.idx = idx
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
                cell._prev = self.cells[-1]
                self.cells[-1]._next = cell
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

    def __repr__(self):
        return f"Lane({self.idx}, cells={self.num_cells})"
