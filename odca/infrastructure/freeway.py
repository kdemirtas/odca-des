"""Freeway: a multi-lane segment with on-ramps and off-ramps."""

from __future__ import annotations

from typing import Dict, List, Optional, Set

import simpy

from odca.infrastructure.cell import Cell, DestinationCell, OriginCell
from odca.infrastructure.lane import Lane
from odca.params import NetworkConfig


def _positive(speed_limit: float, name: str) -> float:
    """`speed_limit` if it is above 0.

    Args:
        speed_limit: cells/s.
        name: the place, for the error message.

    Raises:
        ValueError: the limit is 0 or negative.
    """
    if not speed_limit > 0:
        raise ValueError(f"{name}: speed limit must be above 0, got {speed_limit}")
    return speed_limit


class Origin:
    """A named place where vehicles enter: an `OriginCell` joined to a road cell."""

    def __init__(self, name: str, entry: OriginCell):
        """The origin `name`, entering through `entry`.

        Args:
            name: the origin's name.
            entry: its origin cell.
        """
        self.name = name
        self.entry = entry
        self.cell = entry.road_cell

    def set_speed_limit(self, speed_limit: float):
        """Meter the inflow: vehicles pass the origin cell at most at `speed_limit` (cells/s).

        Args:
            speed_limit: cells/s, > 0; float("inf") removes the meter.

        Raises:
            ValueError: a limit that is not positive (to close an origin, block its road cell).
        """
        self.entry.speed_limit = _positive(speed_limit, self.name)


class Destination:
    """A named place where vehicles leave: past cell `cell_idx - 1`, from `lane` (None: any).

    It has one `DestinationCell` per lane it can be left from.
    """

    def __init__(self, name: str, cell_idx: int, lane: Optional[int], is_offramp: bool):
        """The destination `name`; its exit cells are added by the freeway.

        Args:
            name: the destination's name.
            cell_idx: vehicles leave past cell `cell_idx - 1`.
            lane: the lane it is left from, None for any lane.
            is_offramp: whether it leaves before the segment end.
        """
        self.name = name
        self.cell_idx = cell_idx
        self.lane = lane
        self.is_offramp = is_offramp
        self.cells: List[DestinationCell] = []

    def set_speed_limit(self, speed_limit: float):
        """Throttle the outflow: vehicles leave at most at `speed_limit` (cells/s), per lane.

        Args:
            speed_limit: cells/s, > 0; float("inf") removes the throttle.

        Raises:
            ValueError: a limit that is not positive (to close an exit, block its road cells).
        """
        _positive(speed_limit, self.name)
        for cell in self.cells:
            cell.speed_limit = speed_limit


class Freeway:
    """A multi-lane segment, lane 1 the rightmost, with its named origins and destinations."""

    def __init__(self, env: simpy.Environment, network: NetworkConfig):
        """Build lanes, cells, origins and destinations (D-2026-09-19-26).

        Args:
            env: the SimPy environment the cells belong to.
            network: geometry plus the origins and destinations by name.

        Raises:
            ValueError: an origin or destination outside the lanes or cells.
        """
        self.env = env
        self.network = network
        self.num_lanes = network.num_lanes
        self.num_cells = network.num_cells
        self.speed_limit = network.speed_limit
        self.onramp_cells: Set[int] = set(network.onramp_cells)
        self.offramp_cells: Set[int] = set(network.offramp_cells)
        num_lanes, num_cells, speed_limit = self.num_lanes, self.num_cells, self.speed_limit

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

        self.link_neighbours()

        # Quick lookup by lane index (1-based)
        self._lane_by_idx: Dict[int, Lane] = {l.idx: l for l in self.lanes}
        self._build_endpoints()
        self.cell_incidents: Dict[Cell, object] = {}  # incident records by cell (incident.py)

    def link_neighbours(self):
        """Set every road cell's side and diagonal links from the lane links."""
        for lane in self.lanes:
            for cell in lane.cells:
                left = lane.left.cells[cell.idx] if lane.left else None
                right = lane.right.cells[cell.idx] if lane.right else None
                cell.left, cell.right = left, right
                cell.left_next = left.next if left else None
                cell.left_prev = left.previous if left else None
                cell.right_next = right.next if right else None
                cell.right_prev = right.previous if right else None

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

    def _build_endpoints(self):
        """Create the origins and destinations with their endpoint cells (D-2026-09-19-27)."""
        net = self.network
        self.origins: Dict[str, Origin] = {}
        for name, o in net.origins.items():
            if not (1 <= o.lane <= net.num_lanes and 0 <= o.cell < net.num_cells):
                raise ValueError(f"origin {name!r} at lane {o.lane}, cell {o.cell} is off the road")
            road_cell = self.cell(o.lane, o.cell)
            road_cell.entry = OriginCell(name, road_cell, self.env)
            self.origins[name] = Origin(name, road_cell.entry)
        self.destinations: Dict[str, Destination] = {}
        for name, d in net.destinations.items():
            if not (1 <= d.cell <= net.num_cells) or (
                    d.lane is not None and not 1 <= d.lane <= net.num_lanes):
                raise ValueError(
                    f"destination {name!r} at lane {d.lane}, cell {d.cell} is off the road")
            dest = Destination(name, d.cell, d.lane, d.cell < net.num_cells)
            self.destinations[name] = dest
            lanes = self.lanes if d.lane is None else [self.lane(d.lane)]
            for lane in lanes:
                road_cell = lane.cells[d.cell - 1]
                exit_cell = DestinationCell(name, road_cell, self.env, dest)
                dest.cells.append(exit_cell)
                road_cell.exits.append(exit_cell)

    def origin(self, name: str) -> Origin:
        """The origin called `name`.

        Args:
            name: a key of the network's `origins`.

        Raises:
            ValueError: the network has no such origin.
        """
        if name not in self.origins:
            raise ValueError(f"unknown origin {name!r}; this freeway has {sorted(self.origins)}")
        return self.origins[name]

    def destination(self, name: str) -> Destination:
        """The destination called `name`.

        Args:
            name: a key of the network's `destinations`.

        Raises:
            ValueError: the network has no such destination.
        """
        if name not in self.destinations:
            raise ValueError(f"unknown destination {name!r}; this freeway has "
                             f"{sorted(self.destinations)}")
        return self.destinations[name]

    def __repr__(self):
        return f"Freeway(lanes={self.num_lanes}, cells={self.num_cells})"
