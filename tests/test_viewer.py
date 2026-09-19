"""The viewers read a finished run (D-2026-09-19-34); skipped without the `[viewer]` extra."""

import sys

import numpy as np
import pytest

from odca.simulation.engine import Simulation
from odca.viewer.snapshots import build_snapshots, reconstruct_grid

sys.path.insert(0, "tests/golden/paper_odca_des")
try:
    from config import sim_config
finally:
    sys.path.remove("tests/golden/paper_odca_des")
    sys.modules.pop("config", None)


@pytest.fixture(scope="module")
def result():
    return Simulation(sim_config(sim_duration=40.0, warmup=0.0, seed=3)).run()


def test_grid_places_every_vehicle_on_the_road(result):
    t = 30.0
    on_road = [s for s in build_snapshots(result.vehicles) if s.at(t) is not None]
    grid = reconstruct_grid(build_snapshots(result.vehicles), t, 4, 800)
    assert np.count_nonzero(~np.isnan(grid)) == len(on_road) > 0


def test_time_space_diagram_is_written(result, tmp_path):
    pytest.importorskip("matplotlib")
    import matplotlib
    matplotlib.use("Agg")
    from odca.viewer.animation import plot_trajectories
    plot_trajectories(result, lane_filter=1, save_path=str(tmp_path / "tsd.png"))
    assert (tmp_path / "tsd.png").stat().st_size > 0
