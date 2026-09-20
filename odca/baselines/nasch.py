"""Nagel-Schreckenberg cellular automaton baseline.

Classical NaSch model with synchronous parallel updates and integer speeds.
Used as a comparison baseline for the ODCA-DES framework in Section 4.

Rules (applied in order, synchronously to all vehicles):
  R1. Acceleration:  v = min(v + 1, v_max)
  R2. Deceleration:  v = min(v, gap)      where gap = cells to leader - 1
  R3. Randomization: if rand() < p: v = max(v - 1, 0)
  R4. Movement:      x = x + v

With `cell_v_max` set, R1 reads the limit posted on the cells the vehicle would cross this step
instead of the one road-wide `v_max`, so no vehicle crosses a cell faster than that cell allows.
Unset, which is the default, every cell allows `v_max` and the rules above are unchanged.

Reference: Nagel & Schreckenberg (1992), J. Phys. I France 2, 2221-2229.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Tuple

import numpy as np


@dataclass
class NaSchConfig:
    """NaSch simulation parameters."""
    num_cells: int = 800
    num_lanes: int = 1       # single-lane NaSch for FD comparison
    v_max: int = 5           # integer max speed (cells/timestep)
    slowdown_prob: float = 0.3
    density: float = 0.1     # initial vehicle density (vehicles/cell)
    num_steps: int = 3600    # timesteps (1 step = 1 second)
    warmup_steps: int = 300
    seed: int = 42
    cell_v_max: Optional[Tuple[int, ...]] = None   # per-cell posted limit, None: v_max everywhere


class NaSchSimulation:
    """Single-lane NaSch CA with periodic boundaries."""

    def __init__(self, config: NaSchConfig):
        self.config = config
        self.rng = np.random.default_rng(config.seed)

        if config.cell_v_max is not None and len(config.cell_v_max) != config.num_cells:
            raise ValueError(
                f"cell_v_max has {len(config.cell_v_max)} entries for {config.num_cells} cells"
            )
        self.cell_v_max = (
            np.full(config.num_cells, config.v_max, dtype=int)
            if config.cell_v_max is None
            else np.asarray(config.cell_v_max, dtype=int)
        )

        # Road: -1 = empty, >= 0 = vehicle speed
        self.road = np.full(config.num_cells, -1, dtype=int)

        # Place vehicles randomly at given density
        num_vehicles = int(config.num_cells * config.density)
        positions = self.rng.choice(
            config.num_cells, size=num_vehicles, replace=False
        )
        positions.sort()
        for pos in positions:
            self.road[pos] = self.rng.integers(0, config.v_max + 1)

        self.num_vehicles = num_vehicles

        # Trajectory storage: (timestep, position, speed)
        self.trajectories: List[List[Tuple[int, int, int]]] = [
            [] for _ in range(num_vehicles)
        ]
        self._veh_positions = positions.tolist()

    def _posted(self, pos: int, v: int) -> int:
        """The highest speed that crosses no cell faster than that cell allows.

        Args:
            pos: the vehicle's cell.
            v: the speed it would hold after R1.
        """
        N = self.config.num_cells
        v = min(v, int(self.cell_v_max[pos]))
        while v > 0 and min(int(self.cell_v_max[(pos + d) % N]) for d in range(1, v + 1)) < v:
            v -= 1
        return v

    def _gap(self, pos: int) -> int:
        """Distance to the next vehicle ahead (periodic boundary)."""
        for d in range(1, self.config.num_cells):
            ahead = (pos + d) % self.config.num_cells
            if self.road[ahead] >= 0:
                return d - 1  # gap = distance - 1 (exclude leader's cell)
        return self.config.num_cells - 1  # no leader found

    def step(self):
        """One synchronous NaSch update step."""
        N = self.config.num_cells
        p = self.config.slowdown_prob

        # Collect current state
        positions = []
        speeds = []
        for i in range(N):
            if self.road[i] >= 0:
                positions.append(i)
                speeds.append(self.road[i])

        new_positions = []
        new_speeds = []

        for pos, v in zip(positions, speeds):
            gap = self._gap(pos)

            # R1: Acceleration, up to what the cells ahead allow
            v = self._posted(pos, v + 1)
            # R2: Deceleration
            v = min(v, gap)
            # R3: Randomization
            if self.rng.random() < p and v > 0:
                v -= 1
            # R4: Movement
            new_pos = (pos + v) % N

            new_positions.append(new_pos)
            new_speeds.append(v)

        # Update road
        self.road[:] = -1
        for pos, v in zip(new_positions, new_speeds):
            self.road[pos] = v

        self._veh_positions = new_positions
        return new_positions, new_speeds

    def run(self) -> dict:
        """Run full simulation, collect FD data."""
        flow_data = []      # (density, flow, avg_speed) per timestep
        warmup = self.config.warmup_steps

        for t in range(self.config.num_steps):
            positions, speeds = self.step()

            # Record trajectories
            for i, (pos, v) in enumerate(zip(positions, speeds)):
                self.trajectories[i].append((t, pos, v))

            # Post-warmup: measure FD
            if t >= warmup and speeds:
                avg_speed = np.mean(speeds)
                density = self.num_vehicles / self.config.num_cells
                flow = density * avg_speed
                flow_data.append((density, flow, avg_speed))

        # Aggregate FD
        if flow_data:
            avg_flow = np.mean([f for _, f, _ in flow_data])
            avg_speed = np.mean([s for _, _, s in flow_data])
            density = self.num_vehicles / self.config.num_cells
        else:
            avg_flow = avg_speed = density = 0.0

        return {
            "density": density,
            "flow": avg_flow,
            "speed": avg_speed,
            "num_vehicles": self.num_vehicles,
            "num_steps": self.config.num_steps,
        }


def sweep_density(
    densities: Optional[List[float]] = None,
    config: Optional[NaSchConfig] = None,
) -> List[dict]:
    """Run NaSch at multiple densities to produce a fundamental diagram.

    Returns list of {density, flow, speed} dicts.
    """
    if config is None:
        config = NaSchConfig()
    if densities is None:
        densities = [i / 100 for i in range(1, 100)]

    results = []
    for d in densities:
        cfg = NaSchConfig(
            num_cells=config.num_cells,
            num_lanes=config.num_lanes,
            v_max=config.v_max,
            slowdown_prob=config.slowdown_prob,
            density=d,
            num_steps=config.num_steps,
            warmup_steps=config.warmup_steps,
            seed=config.seed,
        )
        sim = NaSchSimulation(cfg)
        result = sim.run()
        results.append(result)

    return results
