"""Delay is measured against the free-flow speed of each cell (D-2026-09-20-3)."""

import sys

import pytest

from odca.analysis.metrics import delay, travel_time
from odca.params import IncidentConfig, NetworkConfig
from odca.simulation.engine import Simulation

sys.path.insert(0, "tests/golden/paper_odca_des")
try:
    from config import sim_config
finally:
    sys.path.remove("tests/golden/paper_odca_des")
    sys.modules.pop("config", None)

SLOW_ZONE = IncidentConfig(start=0.0, duration=600.0, first_cell=20, last_cell=39,
                           speed_limit=1.3)


def _corridor(**changes):
    """A 60-cell single lane, one vehicle every 20 s, so nobody follows anybody."""
    settings = dict(network=NetworkConfig.corridor(1, 60, 5.2),
                    demand={"mainline_lane_1": {"end_lane_1": 180.0}},
                    sim_duration=600.0, warmup=0.0, seed=3, av_penetration=1.0)
    settings.update(changes)
    return sim_config(**settings)


def _first_completed(result):
    return next(v for v in result.completed_vehicles if v.time_exited is not None)


def test_work_zone_lengthens_the_trip_without_adding_delay():
    free = _first_completed(Simulation(_corridor()).run())
    slowed = _first_completed(Simulation(_corridor(incidents=(SLOW_ZONE,))).run())

    # 20 cells at 1.3 instead of 5.2 cells/s: 15.38 - 3.85 = 11.5 s more driving.
    assert travel_time(slowed) - travel_time(free) > 10.0
    assert delay(free) < 0.01
    # None of it is delay: the limit takes effect on the cell that posts it, at both ends of
    # the zone, so the vehicle drives every cell at exactly what that cell allows.
    assert delay(slowed) < 0.01


def test_a_leader_still_causes_delay():
    """The same slow zone, but 1,800 veh/h: what a vehicle loses to the queue is delay."""
    busy = Simulation(_corridor(demand={"mainline_lane_1": {"end_lane_1": 1800.0}},
                                incidents=(SLOW_ZONE,))).run()
    delays = [delay(v) for v in busy.completed_vehicles if delay(v) is not None]
    assert max(delays) > 5.0


def test_the_limit_takes_effect_on_the_cell_that_posts_it():
    """Entering and leaving a slow stretch, both at the sign (D-2026-09-20-4)."""
    vehicle = _first_completed(Simulation(_corridor(incidents=(SLOW_ZONE,))).run())
    crossing = {}
    for first, second in zip(vehicle.trajectory, vehicle.trajectory[1:]):
        crossing[first.cell_idx] = second.time - first.time

    assert crossing[19] == pytest.approx(1 / 5.2)  # last cell before the zone: full speed
    assert crossing[20] == pytest.approx(1 / 1.3)  # first cell of the zone: already slowed
    assert crossing[39] == pytest.approx(1 / 1.3)  # last cell of the zone: still slowed
    assert crossing[40] == pytest.approx(1 / 5.2)  # first cell after it: back to full speed
