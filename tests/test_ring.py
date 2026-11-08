"""Ring roads with exits (D-2026-11-08-1): off by default; positions wrap, distances to an exit
are taken around the ring, a missed exit is a lap away, and a platoon member bound for an exit
lane splits off on a two-lane ring as on a freeway."""

from dataclasses import replace

import pytest
import simpy

from odca.entity.driver import AutonomousDriver
from odca.entity.vehicle import Direction
from odca.infrastructure.freeway import Freeway
from odca.params import (
    ControllerConfig, DestinationConfig, NetworkConfig, OriginConfig, PlatoonConfig, SimConfig,
    validate,
)
from odca.simulation.engine import Simulation

NUM_CELLS = 200
PLATOON = PlatoonConfig(strategy="dcp", dt=1.0, max_platoon_size=10, formation_gap=5,
                        formation_speed_diff=1.0, dest_cluster_threshold=100,
                        min_shared_path=0, split_lookahead=150)


def _network(ring=True, num_lanes=2):
    destinations = {"exit_a": DestinationConfig(cell=50, lane=1),
                    "exit_any": DestinationConfig(cell=100),
                    "end": DestinationConfig(cell=NUM_CELLS)}
    return NetworkConfig(num_lanes=num_lanes, num_cells=NUM_CELLS, speed_limit=5.2,
                         origins={"start": OriginConfig(lane=1)}, destinations=destinations,
                         ring=ring)


def _config(ring=True, platoon=False, sim_duration=120.0):
    base = {"network": _network(ring), "demand": {},
            "hdv_vehicle": "odca://hdv_vehicle.yaml", "hdv_driver": "odca://hdv_driver.yaml",
            "av_vehicle": "odca://av_vehicle.yaml", "av_driver": "odca://av_driver.yaml",
            "sim_duration": sim_duration, "warmup": 0.0}
    config = validate(SimConfig, base)
    if platoon:
        config = replace(config, controller=ControllerConfig(platoon=PLATOON))
    return config


def _place(sim, specs):
    """Put vehicles on the road at t=0: (autonomous, lane, cell, destination) each."""
    vehicles = []
    for autonomous, lane, cell, destination in specs:
        origin = sim.freeway.lane(lane).cells[cell]
        vehicle = sim.factory.build(autonomous, origin, sim.freeway.destination(destination))
        sim.env.process(vehicle.start())
        vehicles.append(vehicle)
    sim.env.run(until=sim.env.now + 1e-6)
    return vehicles


def test_ring_is_off_by_default():
    assert NetworkConfig.corridor(2, 100, 5.2).ring is False
    freeway = Freeway(simpy.Environment(), _network(ring=False))
    assert not freeway.ring and freeway.lane(1).last.next is None
    assert not freeway.destination("end").is_offramp


def test_a_ring_joins_every_lane_and_every_exit_is_an_offramp():
    freeway = Freeway(simpy.Environment(), _network())
    for lane in freeway.lanes:
        assert lane.last.next is lane.first and lane.first.previous is lane.last
    assert freeway.lane(2).last.right_next is freeway.lane(1).first
    assert all(d.is_offramp for d in freeway.destinations.values())


def test_distances_are_taken_around_the_ring():
    ring = Freeway(simpy.Environment(), _network()).lane(1)
    road = Freeway(simpy.Environment(), _network(ring=False)).lane(1)
    assert ring.cells_ahead(190, 50) == 60 and road.cells_ahead(190, 50) == -140
    assert ring.spacing(198, 3) == 5 and road.spacing(198, 3) == 195
    sim = Simulation(_config())
    (vehicle,) = _place(sim, [(True, 1, 190, "exit_a")])
    assert vehicle.cells_to_destination() == 60
    assert vehicle.initial_distance == 60


def test_a_vehicle_passing_cell_0_drives_on_to_its_exit():
    sim = Simulation(_config())
    (vehicle,) = _place(sim, [(True, 1, 195, "exit_a")])
    sim.env.run(until=5.0)
    assert vehicle.active and vehicle.time_exited is None
    assert 0 < vehicle.cell.idx < 49
    sim.env.run(until=60.0)
    cells = [record.cell_idx for record in vehicle.trajectory]
    assert vehicle.time_exited is not None
    assert cells[:6] == [195, 196, 197, 198, 199, 0] and cells[-1] == 49
    assert vehicle.count_missed_exits == 0


def test_a_lane_joined_by_make_periodic_alone_keeps_open_road_exits():
    """Without `ring`, an exit behind the vehicle is passed at once, as before."""
    config = replace(_config(ring=False), sim_duration=5.0)
    sim = Simulation(config)
    sim.freeway.lane(1).make_periodic()
    (vehicle,) = _place(sim, [(True, 1, 195, "exit_any")])
    sim.env.run(until=5.0)
    assert vehicle.time_exited is not None and vehicle.trajectory[-1].cell_idx == 195


def test_a_missed_exit_on_a_ring_is_a_lap_away_and_counted_once():
    sim = Simulation(_config())
    (vehicle,) = _place(sim, [(True, 2, 50, "exit_a")])   # beside the exit, outside its lane
    assert vehicle.cells_to_destination() == 0 and vehicle.active
    sim.env.run(until=3.0)
    assert vehicle.active and vehicle.count_missed_exits == 1
    assert vehicle.cells_to_destination() > NUM_CELLS - 20


def _stuck_outside_its_exit_lane(monkeypatch, missed_exit_laps):
    """An AV in lane 2 bound for `exit_a` (cell 50, lane 1) that never changes lanes."""
    monkeypatch.setattr(AutonomousDriver, "evaluate_direction",
                        lambda self: self.vehicle.request_direction(Direction.FORWARD))
    config = _config(sim_duration=200.0)
    network = replace(config.network, missed_exit_laps=missed_exit_laps)
    sim = Simulation(replace(config, network=network))
    (vehicle,) = _place(sim, [(True, 2, 40, "exit_a")])
    sim.env.process(sim.controller.run())
    sim.env.run(until=200.0)
    return vehicle


def test_missed_exit_laps_defaults_to_one():
    assert _network().missed_exit_laps == 1


def test_one_more_lap_then_the_next_exit_by_default(monkeypatch):
    vehicle = _stuck_outside_its_exit_lane(monkeypatch, 1)
    assert vehicle.count_missed_exits == 2          # cell 50 missed twice
    assert vehicle.destination_cell_idx == 100      # then exit_any, the next one ahead
    assert vehicle.time_exited is not None and vehicle.trajectory[-1].cell_idx == 99
    passes_of_cell_50 = sum(1 for r in vehicle.trajectory if r.cell_idx == 50)
    assert passes_of_cell_50 == 2


def test_zero_laps_takes_the_next_exit_at_once(monkeypatch):
    vehicle = _stuck_outside_its_exit_lane(monkeypatch, 0)
    assert vehicle.count_missed_exits == 1
    assert vehicle.time_exited is not None and vehicle.trajectory[-1].cell_idx == 99
    assert sum(1 for r in vehicle.trajectory if r.cell_idx == 50) == 1


def test_a_negative_lap_limit_is_refused():
    with pytest.raises(ValueError, match="missed_exit_laps"):
        Freeway(simpy.Environment(), replace(_network(), missed_exit_laps=-1))


def test_a_platoon_forms_across_cell_0_with_the_front_member_leading():
    sim = Simulation(_config(platoon=True))
    tail, middle, front = _place(sim, [(True, 2, 198, "exit_any"), (True, 2, 199, "exit_any"),
                                       (True, 2, 1, "exit_any")])
    sim.controller._evaluate_formations([tail, middle, front])
    platoon = front.driver.platoon
    assert platoon is not None and platoon.members == [front, middle, tail]


def test_a_destination_split_is_counted_on_a_two_lane_ring():
    sim = Simulation(_config(platoon=True))
    front, middle, tail = _place(sim, [(True, 2, 1, "exit_any"), (True, 2, 0, "exit_any"),
                                       (True, 2, 199, "exit_a")])
    platoon = sim.controller.form([front, middle, tail])
    sim.controller._evaluate_splits()
    assert platoon.members == [front, middle] and tail.driver.platoon is None
    assert sim.controller.statistics().destination_splits == 1


def test_a_run_on_a_two_lane_ring_splits_and_every_member_reaches_its_exit():
    sim = Simulation(_config(platoon=True, sim_duration=120.0))
    members = _place(sim, [(True, 2, 160, "exit_any"), (True, 2, 159, "exit_any"),
                           (True, 2, 158, "exit_a")])
    sim.controller.form(members)
    result = sim.run()
    assert result.platoons.destination_splits == 1
    assert all(m.time_exited is not None for m in members)
    assert members[2].trajectory[-1].cell_idx in (49, 50)
    assert members[2].trajectory[-1].lane_idx == 1
