"""Vehicle trajectories indexed for lookup by time, shared by the viewers."""

from __future__ import annotations

from bisect import bisect_right
from typing import List, Optional, Tuple

import numpy as np

from odca.entity.vehicle import Vehicle


class VehicleSnapshot:
    """One vehicle's trajectory, indexed for its position at any time."""

    __slots__ = ("vid", "kind", "times", "cells", "lanes", "speeds", "t_enter", "t_exit")

    def __init__(self, vehicle: Vehicle):
        """Index `vehicle`'s trajectory.

        Args:
            vehicle: a vehicle of a finished run.
        """
        self.vid = vehicle.id
        self.kind = vehicle.kind
        traj = vehicle.trajectory
        self.times = [r.time for r in traj]
        self.cells = [r.cell_idx for r in traj]
        self.lanes = [r.lane_idx for r in traj]
        self.speeds = [r.speed for r in traj]
        self.t_enter = vehicle.time_entered
        self.t_exit = vehicle.time_exited

    def at(self, t: float) -> Optional[Tuple[int, int, float]]:
        """(cell, lane, speed) at time `t`, or None when off the road.

        Args:
            t: simulation time (s).
        """
        if self.t_enter is None or t < self.t_enter:
            return None
        if self.t_exit is not None and t >= self.t_exit:
            return None
        idx = bisect_right(self.times, t) - 1
        if idx < 0:
            return None
        return self.cells[idx], self.lanes[idx], self.speeds[idx]


def build_snapshots(vehicles: List[Vehicle]) -> List[VehicleSnapshot]:
    """Snapshots of the vehicles that entered the road.

    Args:
        vehicles: a run's vehicles.
    """
    return [VehicleSnapshot(v) for v in vehicles if v.trajectory]


def reconstruct_grid(snapshots: List[VehicleSnapshot], t: float, num_lanes: int,
                     num_cells: int) -> np.ndarray:
    """A (lanes, cells) array of speeds at time `t`, NaN where empty; lane 1 is the last row.

    Args:
        snapshots: the indexed trajectories.
        t: simulation time (s).
        num_lanes: lanes of the road.
        num_cells: cells per lane.
    """
    grid = np.full((num_lanes, num_cells), np.nan)
    for snap in snapshots:
        pos = snap.at(t)
        if pos is None:
            continue
        cell_idx, lane_idx, speed = pos
        if 0 <= cell_idx < num_cells and 1 <= lane_idx <= num_lanes:
            grid[num_lanes - lane_idx, cell_idx] = speed
    return grid
