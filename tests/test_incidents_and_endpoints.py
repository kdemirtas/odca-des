"""Throttled endpoints (D-2026-09-19-27) and incidents (D-2026-09-19-28) on a short corridor."""

import sys

import pytest

from odca.params import IncidentConfig, NetworkConfig
from odca.simulation.engine import Simulation

sys.path.insert(0, "tests/golden/paper_odca_des")
try:
    from config import sim_config
finally:
    sys.path.remove("tests/golden/paper_odca_des")
    sys.modules.pop("config", None)


def _corridor(**changes):
    return sim_config(network=NetworkConfig.corridor(1, 60, 5.2),
                      demand={"mainline_lane_1": {"end_lane_1": 1800.0}},
                      sim_duration=600.0, warmup=0.0, seed=3, **changes)


def _run(config, before_run=None):
    sim = Simulation(config)
    if before_run:
        before_run(sim)
    return sim, sim.run()


def test_throttled_exit_caps_outflow():
    _, plain = _run(_corridor())
    _, throttled = _run(_corridor(), lambda sim: sim.freeway.destination("end_lane_1")
                        .set_speed_limit(0.25))
    tau = 1.5
    cap = 600.0 / (tau + 1 / 0.25) * 1.1  # 3600 / (tau + 1/v) veh/h over 600 s, 10% slack
    assert throttled.num_completed <= cap < plain.num_completed


def test_metered_origin_caps_inflow():
    _, metered = _run(_corridor(), lambda sim: sim.freeway.origin("mainline_lane_1")
                      .set_speed_limit(0.25))
    entered = sum(1 for v in metered.vehicles if v.time_entered is not None)
    assert entered <= 600.0 / (1.5 + 1 / 0.25) * 1.1


def test_incident_blocks_then_restores():
    incident = IncidentConfig(start=100.0, duration=200.0, lane=1, first_cell=30, last_cell=35)
    sim, blocked = _run(_corridor(incidents=[incident]))
    _, plain = _run(_corridor())
    assert blocked.num_completed < plain.num_completed
    assert not any(cell.blocked for cell in sim.freeway.lane(1).cells)  # restored


def test_incident_can_throttle_a_destination():
    incident = IncidentConfig(start=0.0, duration=600.0, place="end_lane_1", speed_limit=0.25)
    _, throttled = _run(_corridor(incidents=[incident]))
    assert throttled.num_completed <= 600.0 / (1.5 + 1 / 0.25) * 1.1


def test_a_place_cannot_be_blocked():
    with pytest.raises(ValueError, match="throttled, not blocked"):
        Simulation(_corridor(incidents=[IncidentConfig(start=0, duration=1, place="end_lane_1")]))


def test_overlapping_incidents_stack_and_all_end():
    import simpy
    from odca.infrastructure.freeway import Freeway
    from odca.infrastructure.incident import Incident
    env = simpy.Environment()
    freeway = Freeway(env, NetworkConfig.corridor(1, 60, 5.2))
    wide = Incident(IncidentConfig(start=100, duration=300, lane=1, first_cell=10, last_cell=20),
                    freeway)
    inner = Incident(IncidentConfig(start=200, duration=400, lane=1, first_cell=15,
                                    last_cell=18, speed_limit=1.0), freeway)
    env.process(wide.run(env))
    env.process(inner.run(env))
    cell, outer_only = freeway.cell(1, 16), freeway.cell(1, 12)
    env.run(until=450)  # wide has ended, inner still slows 15-18
    assert not cell.blocked and cell.speed_limit == 1.0 and not outer_only.blocked
    env.run(until=700)  # both ended: the cells are as they were
    assert not cell.blocked and cell.speed_limit == 5.2


@pytest.mark.parametrize("limit", [0.0, -1.0])
def test_a_limit_must_be_positive(limit):
    with pytest.raises(ValueError, match="above 0"):
        Simulation(_corridor(incidents=[IncidentConfig(start=0, duration=1, place="end_lane_1",
                                                       speed_limit=limit)]))
    sim = Simulation(_corridor())
    with pytest.raises(ValueError, match="above 0"):
        sim.freeway.destination("end_lane_1").set_speed_limit(limit)
    with pytest.raises(ValueError, match="above 0"):
        sim.freeway.origin("mainline_lane_1").set_speed_limit(limit)


def test_missed_offramp_takes_the_next_ramp_lane():
    from types import SimpleNamespace
    from odca.entity.vehicle import Vehicle
    from odca.infrastructure.freeway import Freeway
    from odca.params import DestinationConfig, OriginConfig
    import simpy
    network = NetworkConfig(num_lanes=3, num_cells=500, speed_limit=5.2,
                            origins={"mainline_lane_1": OriginConfig(1)},
                            destinations={"ramp_a": DestinationConfig(200, 1),
                                          "ramp_b": DestinationConfig(400, 3)})
    freeway = Freeway(simpy.Environment(), network)
    vehicle = SimpleNamespace(cell=freeway.cell(2, 210), destination_cell_idx=200,
                              destination_lane=1, count_missed_exits=0)
    Vehicle._retarget_missed_exit(vehicle)
    assert (vehicle.destination_cell_idx, vehicle.destination_lane) == (400, 3)
