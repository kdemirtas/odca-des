"""Delay is measured against the free-flow speed of each cell (D-2026-09-20-3)."""

import sys

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
    # Almost none of it is delay: the vehicle drives every cell at what that cell allows.
    # What is left is one cell of it. A vehicle crosses a cell at the speed it chose on
    # arriving in the previous one, so it carries the work zone's speed one cell past the
    # zone: 1/1.3 - 1/5.2 = 0.577 s (BACKLOG B11).
    assert delay(slowed) < 2 * (1.0 / 1.3 - 1.0 / 5.2)


def test_a_leader_still_causes_delay():
    """The same slow zone, but 1,800 veh/h: what a vehicle loses to the queue is delay."""
    busy = Simulation(_corridor(demand={"mainline_lane_1": {"end_lane_1": 1800.0}},
                                incidents=(SLOW_ZONE,))).run()
    delays = [delay(v) for v in busy.completed_vehicles if delay(v) is not None]
    assert max(delays) > 5.0
