"""Incidents: cells blocked or slowed for a while, then restored (D-2026-09-19-28)."""

from __future__ import annotations

import logging
from typing import List

import simpy

from odca.infrastructure.cell import Cell
from odca.infrastructure.freeway import Freeway
from odca.params import ConfigMixin, IncidentConfig

logger = logging.getLogger(__name__)


class Incident(ConfigMixin):
    """One incident on a freeway: `run` is its SimPy process."""

    Config = IncidentConfig

    def __init__(self, cfg: IncidentConfig, freeway: Freeway):
        """Resolve the cells the incident acts on.

        Args:
            cfg: when, where and what.
            freeway: the freeway it happens on.

        Raises:
            ValueError: a place that is blocked (only throttling is allowed there), an
                unknown place, or a speed limit that is not above 0.
        """
        self.cfg = cfg
        self.freeway = freeway
        self.cells = self._cells(cfg, freeway)

    @staticmethod
    def _cells(cfg: IncidentConfig, freeway: Freeway) -> List[Cell]:
        """The cells `cfg` names.

        Args:
            cfg: the incident config.
            freeway: the freeway it happens on.
        """
        if cfg.speed_limit is not None and not cfg.speed_limit > 0:
            raise ValueError(f"incident speed limit must be above 0 (None blocks the cells), "
                             f"got {cfg.speed_limit}")
        if cfg.place is not None:
            if cfg.speed_limit is None:
                raise ValueError(f"incident at {cfg.place!r}: an origin or destination can "
                                 "be throttled, not blocked")
            if cfg.place in freeway.origins:
                return [freeway.origin(cfg.place).entry]
            return list(freeway.destination(cfg.place).cells)
        lanes = freeway.lanes if cfg.lane is None else [freeway.lane(cfg.lane)]
        cells = []
        for lane in lanes:
            last = cfg.last_cell if cfg.last_cell >= 0 else len(lane.cells) - 1
            cells.extend(lane.cells[cfg.first_cell:last + 1])
        return cells

    def run(self, env: simpy.Environment):
        """Wait for the start, act on the cells for the duration, then let them go.

        Overlapping incidents stack: a cell is blocked while any incident blocks it, its speed
        limit is the lowest of its own and every active incident's, and it returns to its own
        state when the last one ends.

        Args:
            env: the SimPy environment.
        """
        yield env.timeout(self.cfg.start)
        for cell in self.cells:
            _CellIncidents.of(self.freeway, cell).add(self)
        logger.info("t=%.0f incident on: %d cells", env.now, len(self.cells))
        yield env.timeout(self.cfg.duration)
        for cell in self.cells:
            _CellIncidents.of(self.freeway, cell).remove(self)
        logger.info("t=%.0f incident resolved", env.now)


class _CellIncidents:
    """A cell's own state and the incidents acting on it now; kept per freeway."""

    def __init__(self, cell: Cell):
        """Remember `cell`'s own state.

        Args:
            cell: the cell.
        """
        self.cell = cell
        self.blocked, self.speed_limit = cell.blocked, cell.speed_limit
        self.active: List[Incident] = []

    @classmethod
    def of(cls, freeway: Freeway, cell: Cell) -> "_CellIncidents":
        """The record for `cell`, created on first use.

        Args:
            freeway: the freeway holding the records.
            cell: the cell.
        """
        records = freeway.cell_incidents
        if cell not in records:
            records[cell] = cls(cell)
        return records[cell]

    def add(self, incident: Incident):
        """An incident starts acting on the cell.

        Args:
            incident: the incident.
        """
        if not self.active:  # the cell's own state, as it is before any incident
            self.blocked, self.speed_limit = self.cell.blocked, self.cell.speed_limit
        self.active.append(incident)
        self._apply()

    def remove(self, incident: Incident):
        """An incident stops acting on the cell.

        Args:
            incident: the incident.
        """
        self.active.remove(incident)
        self._apply()

    def _apply(self):
        """Set the cell from its own state and the active incidents."""
        limits = [i.cfg.speed_limit for i in self.active if i.cfg.speed_limit is not None]
        self.cell.blocked = self.blocked or any(i.cfg.speed_limit is None for i in self.active)
        self.cell.speed_limit = min([self.speed_limit, *limits])
