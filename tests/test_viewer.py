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


def test_time_window_bounds_both_ends(result, tmp_path, monkeypatch):
    pytest.importorskip("matplotlib")
    import matplotlib
    matplotlib.use("Agg")
    from matplotlib.collections import LineCollection
    from odca.viewer import animation
    drawn = []
    real = LineCollection.__init__

    def keep(self, segments, *args, **kwargs):
        drawn.extend(segments)
        real(self, segments, *args, **kwargs)
    monkeypatch.setattr(LineCollection, "__init__", keep)
    animation.plot_trajectories(result, t_range=(10.0, 20.0), save_path=str(tmp_path / "w.png"))
    times = [t for segment in drawn for t, _ in segment]
    assert times and min(times) >= 10.0 and max(times) <= 20.0


def test_playback_draws_a_frame_headless(result, monkeypatch):
    pytest.importorskip("pygame")
    monkeypatch.setenv("SDL_VIDEODRIVER", "dummy")
    from odca.viewer.playback import TrafficVisualizer
    viz = TrafficVisualizer.from_result(result)
    active = [(s, *s.at(30.0)) for s in viz.snapshots if s.at(30.0)]
    viz._draw_road()
    viz._draw_vehicles(active)
    viz._draw_hud(len(active))
    assert viz.num_lanes == 4 and len(active) > 0
