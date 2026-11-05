"""Train platooning (D-2026-11-05-1, D-2026-11-05-3): off by default; the leader is the front
member; the train becomes and stays contiguous with no other vehicle inside; a lane change moves
the whole chain or none of it; splits, merges and the strategies' grouping."""

from dataclasses import replace

import pytest

from odca.entity.controller import AutonomousController
from odca.entity.driver import AutonomousDriver
from odca.entity.vehicle import Direction, LaneChangeReason
from odca.params import (
    ControllerConfig, DestinationConfig, NetworkConfig, OriginConfig, PlatoonConfig, SimConfig,
    validate,
)
from odca.platoon import (
    Platoon, PlatoonController, av_unit_size_at, count_av_units, pooled, section_counts,
)
from odca.simulation.engine import Simulation

PLATOON = PlatoonConfig(strategy="dcp", dt=1.0, max_platoon_size=10, formation_gap=5,
                        formation_speed_diff=1.0, dest_cluster_threshold=100,
                        min_shared_path=0, split_lookahead=150)


def _config(strategy="dcp", num_lanes=2, **platoon):
    network = NetworkConfig(
        num_lanes=num_lanes, num_cells=400, speed_limit=5.2,
        origins={"start": OriginConfig(lane=1)},
        destinations={"offramp": DestinationConfig(cell=300, lane=1),
                      "end": DestinationConfig(cell=400)})
    base = {"network": network, "demand": {},
            "hdv_vehicle": "odca://hdv_vehicle.yaml", "hdv_driver": "odca://hdv_driver.yaml",
            "av_vehicle": "odca://av_vehicle.yaml", "av_driver": "odca://av_driver.yaml",
            "sim_duration": 60.0, "warmup": 0.0}
    config = validate(SimConfig, base)
    controller = ControllerConfig(platoon=replace(PLATOON, strategy=strategy, **platoon))
    return replace(config, controller=controller)


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


def test_platooning_is_off_by_default():
    assert ControllerConfig().platoon is None
    config = replace(_config(), controller=ControllerConfig())
    sim = Simulation(config)
    assert type(sim.controller) is AutonomousController
    assert sim.run().platoons is None


def test_an_unknown_strategy_raises():
    with pytest.raises(ValueError, match="dpc"):
        replace(PLATOON, strategy="dpc")


def test_formation_puts_the_leader_in_front():
    sim = Simulation(_config())
    rear, middle, front = _place(sim, [(True, 1, 10, "end"), (True, 1, 13, "end"),
                                       (True, 1, 16, "end")])
    sim.controller._evaluate_formations([rear, middle, front])
    platoon = front.driver.platoon
    assert platoon is not None and platoon.members == [front, middle, rear]
    assert platoon.leader is front and platoon.tail is rear


def test_only_the_tail_keeps_its_tau():
    sim = Simulation(_config())
    vehicles = _place(sim, [(True, 1, 12, "end"), (True, 1, 11, "end"), (True, 1, 10, "end")])
    platoon = sim.controller.form(vehicles)
    tau = vehicles[0].driver.tau
    assert [v.driver.release_tau for v in vehicles] == [0.0, 0.0, tau]
    platoon.dissolve()
    assert [v.driver.release_tau for v in vehicles] == [tau, tau, tau]


def test_no_human_driven_vehicle_inside_a_platoon():
    sim = Simulation(_config())
    rear, _, front = _place(sim, [(True, 1, 10, "end"), (False, 1, 12, "end"),
                                  (True, 1, 14, "end")])
    sim.controller._evaluate_formations([rear, front])
    assert rear.driver.platoon is None and front.driver.platoon is None


def test_a_cut_in_breaks_the_chain():
    sim = Simulation(_config())
    front, rear = _place(sim, [(True, 1, 14, "end"), (True, 1, 10, "end")])
    sim.controller.form([front, rear])
    _place(sim, [(False, 1, 12, "end")])
    sim.controller._check_chains()
    assert front.driver.platoon is None and rear.driver.platoon is None
    assert sim.controller.statistics().chain_breaks == 1


def test_the_train_closes_up_and_moves_as_one():
    config = replace(_config(num_lanes=1), sim_duration=20.0)
    sim = Simulation(config)
    members = _place(sim, [(True, 1, 20, "end"), (True, 1, 17, "end"), (True, 1, 14, "end")])
    platoon = sim.controller.form(members)
    sim.env.process(sim.controller.run())
    sim.env.run(until=20.0)
    cells = [m.cell.idx for m in platoon.members]
    assert cells == [cells[0], cells[0] - 1, cells[0] - 2]
    speeds = {round(m.speed, 9) for m in platoon.members}
    assert len(speeds) == 1


def test_a_lane_change_needs_the_whole_target_stretch_free():
    sim = Simulation(_config())
    members = _place(sim, [(True, 1, 12, "end"), (True, 1, 11, "end"), (True, 1, 10, "end")])
    platoon = sim.controller.form(members)
    assert [c.idx for c in platoon.target_cells(Direction.LEFT)] == [11, 12, 13]
    assert platoon.target_lane_free(Direction.LEFT)
    assert platoon.target_cells(Direction.RIGHT) is None   # no lane to the right of lane 1
    _place(sim, [(False, 2, 12, "end")])
    assert not platoon.target_lane_free(Direction.LEFT)


def test_followers_ask_for_the_leaders_lane_change():
    sim = Simulation(_config(train_lane_changes=True))
    leader, follower = _place(sim, [(True, 1, 11, "end"), (True, 1, 10, "end")])
    sim.controller.form([leader, follower])
    leader.request_direction(Direction.LEFT, LaneChangeReason.MLC_DESTINATION)
    follower.driver.evaluate_direction()
    assert follower.desired_direction is Direction.LEFT
    assert follower.direction_reason is LaneChangeReason.MLC_DESTINATION


def test_the_whole_chain_changes_lanes():
    config = replace(_config(train_lane_changes=True), sim_duration=10.0)
    sim = Simulation(config)
    members = _place(sim, [(True, 1, 12, "end"), (True, 1, 11, "end"), (True, 1, 10, "end")])
    platoon = sim.controller.form(members)
    for member in members:
        member.request_direction(Direction.LEFT, LaneChangeReason.DLC)
    sim.env.run(until=2.0)
    assert platoon.active and {m.cell.lane.idx for m in members} == {2}


@pytest.mark.parametrize("train_lane_changes,room", [(True, False), (False, True)])
def test_a_refused_leader_stays_in_lane_with_its_train(monkeypatch, train_lane_changes, room):
    sim = Simulation(_config(train_lane_changes=train_lane_changes))
    leader, follower = _place(sim, [(True, 1, 11, "end"), (True, 1, 10, "end")])
    sim.controller.form([leader, follower])
    if not room:
        _place(sim, [(False, 2, 11, "end")])
    monkeypatch.setattr(
        AutonomousDriver, "evaluate_direction",
        lambda self: self.vehicle.request_direction(Direction.LEFT, LaneChangeReason.DLC))
    leader.driver.evaluate_direction()
    assert leader.desired_direction is Direction.FORWARD
    assert follower.desired_direction is Direction.FORWARD
    assert sim.controller.statistics().lane_changes_blocked == 1


def test_lane_changes_of_the_train_are_off_by_default():
    assert PlatoonConfig.__dataclass_fields__["train_lane_changes"].default is False


def test_remove_split_merge_and_dissolve():
    sim = Simulation(_config())
    vehicles = _place(sim, [(True, 1, 20 - i, "end") for i in range(5)])
    controller = sim.controller
    platoon = controller.form(vehicles)
    controller._remove(platoon, vehicles[2])   # middle: two parts of two
    assert platoon.members == vehicles[:2]
    rear = vehicles[3].driver.platoon
    assert rear is not None and rear.members == vehicles[3:]
    assert vehicles[2].driver.platoon is None
    platoon.merge(rear)
    assert platoon.members == vehicles[:2] + vehicles[3:] and not rear.active
    back = platoon.split_at(3)
    assert back == [vehicles[4]] and platoon.size == 3
    controller._remove(platoon, vehicles[0])   # the leader: the next one leads
    assert platoon.leader is vehicles[1]
    controller._remove(platoon, vehicles[1])   # one left: dissolved
    assert not platoon.active and all(v.driver.platoon is None for v in vehicles)
    assert controller.count_size_one_dissolutions == 1


def test_merge_joins_a_platoon_just_behind():
    sim = Simulation(_config())
    vehicles = _place(sim, [(True, 1, 20 - i, "end") for i in (0, 1, 4, 5)])
    controller = sim.controller
    ahead, behind = controller.form(vehicles[:2]), controller.form(vehicles[2:])
    controller._evaluate_merges()
    assert ahead.members == vehicles and not behind.active
    assert controller.count_merges == 1


@pytest.mark.parametrize("strategy,expected", [
    ("naive", [True, True, True]),
    ("emp", [True, False, False]),
    ("dcp", [True, True, False]),
])
def test_strategies_group_by_destination(strategy, expected):
    sim = Simulation(_config(strategy))
    first = _place(sim, [(True, 1, 50, "offramp")])[0]
    others = _place(sim, [(True, 1, 49, "offramp"), (True, 1, 48, "end"),
                          (True, 1, 47, "end")])
    # the third pair: destinations 300 and 450 apart by 150 cells, beyond the dcp threshold
    others[2].destination_cell_idx = 450
    assert [sim.controller.compatible(first, other) for other in others] == expected


def test_a_through_vehicle_is_not_split_off_at_the_last_ramp():
    sim = Simulation(_config())
    vehicles = _place(sim, [(True, 1, 299 - i, "end") for i in range(3)])
    platoon = sim.controller.form(vehicles)
    sim.controller._evaluate_splits()
    assert platoon.active and platoon.size == 3
    assert sim.controller.count_destination_splits == 0


def test_a_member_bound_for_the_ramp_splits_off_before_it():
    sim = Simulation(_config())
    vehicles = _place(sim, [(True, 2, 200, "end"), (True, 2, 199, "end"),
                            (True, 2, 198, "offramp")])
    platoon = sim.controller.form(vehicles)
    sim.controller._evaluate_splits()
    assert platoon.members == vehicles[:2] and vehicles[2].driver.platoon is None
    stats = sim.controller.statistics()
    assert (stats.destination_splits, stats.end_of_trip_dissolutions,
            stats.size_one_dissolutions) == (1, 0, 0)


def test_a_member_in_the_exit_lane_stays_until_it_leaves_the_road():
    sim = Simulation(_config())
    vehicles = _place(sim, [(True, 1, 200, "end"), (True, 1, 199, "offramp")])
    platoon = sim.controller.form(vehicles)
    sim.controller._evaluate_splits()
    assert platoon.active and platoon.size == 2


def test_a_platoon_all_leaving_is_one_end_of_trip_dissolution():
    sim = Simulation(_config())
    vehicles = _place(sim, [(True, 2, 200 - i, "offramp") for i in range(3)])
    platoon = sim.controller.form(vehicles)
    sim.controller._evaluate_splits()
    assert not platoon.active
    stats = sim.controller.statistics()
    assert (stats.destination_splits, stats.end_of_trip_dissolutions,
            stats.size_one_dissolutions) == (0, 1, 0)


def test_a_two_member_platoon_split_is_also_a_size_one_dissolution():
    sim = Simulation(_config())
    vehicles = _place(sim, [(True, 2, 200, "end"), (True, 2, 199, "offramp")])
    sim.controller.form(vehicles)
    sim.controller._evaluate_splits()
    stats = sim.controller.statistics()
    assert (stats.destination_splits, stats.size_one_dissolutions) == (1, 1)


def test_unit_size_counts_a_solo_av_as_a_unit_of_one():
    sim = Simulation(_config(num_lanes=1))
    platooned = _place(sim, [(True, 1, 100 - i, "end") for i in range(5)])
    solos = _place(sim, [(True, 1, 50, "end"), (True, 1, 30, "end")])
    sim.controller.form(platooned)
    sim.controller._sample_sizes(platooned + solos)
    stats = sim.controller.statistics()
    assert stats.avg_av_unit_size_on_road == pytest.approx(7 / 3)
    assert stats.avg_platoon_size == 5


def test_placed_platoons_and_statistics():
    config = replace(_config(num_lanes=1), sim_duration=30.0)
    sim = Simulation(config)
    sim.seed_platoons(platoon_size=3, gap=4, destination="end")
    placed = [p for p in sim.controller.platoons]
    assert all(p.leader.cell is None for p in placed)  # placed, entering at the first step
    result = sim.run()
    assert isinstance(sim.controller, PlatoonController)
    assert result.platoons.avg_platoon_size >= 2.0
    assert 1.0 <= result.platoons.avg_av_unit_size_on_road <= result.platoons.avg_platoon_size
    assert result.platoons.max_platoon_size <= PLATOON.max_platoon_size


def test_the_platoon_needs_two_members():
    with pytest.raises(ValueError):
        Platoon(0, [])


def test_section_count_counts_a_platoon_once_and_a_solo_av_as_one():
    config = replace(_config(num_lanes=1), sim_duration=40.0)
    sim = Simulation(config)
    platooned = _place(sim, [(True, 1, 60 - i, "end") for i in range(5)])
    solos = _place(sim, [(True, 1, 40, "end"), (True, 1, 30, "end")])
    sim.controller.form(platooned)
    sim.run()
    vehicles = platooned + solos
    count = count_av_units(vehicles, 100, 0.0)
    assert (count.avs, count.units) == (7, 3)
    assert av_unit_size_at(vehicles, [100, 150], 0.0) == pytest.approx(7 / 3)


def test_train_lane_change_decisions_are_logged_by_size(monkeypatch):
    sim = Simulation(_config(train_lane_changes=True))
    members = _place(sim, [(True, 1, 12 - i, "end") for i in range(3)])
    sim.controller.form(members)
    monkeypatch.setattr(
        AutonomousDriver, "evaluate_direction",
        lambda self: self.vehicle.request_direction(Direction.LEFT, LaneChangeReason.DLC))
    members[0].driver.evaluate_direction()
    _place(sim, [(False, 2, 11, "end")])
    members[0].driver.evaluate_direction()
    stats = sim.controller.statistics()
    assert stats.train_lc_attempts_by_size == {"3": 2}
    assert stats.train_lc_granted_by_size == {"3": 1}


def test_an_emp_platoon_reaching_its_exit_makes_no_destination_split():
    config = replace(_config("emp", num_lanes=1), sim_duration=120.0)
    sim = Simulation(config)
    members = _place(sim, [(True, 1, 250 - i, "offramp") for i in range(4)])
    platoon = sim.controller.form(members)
    sim.env.process(sim.controller.run())
    sim.env.run(until=120.0)
    stats = sim.controller.statistics()
    assert all(m.time_exited is not None for m in members)
    assert not platoon.active
    assert stats.destination_splits == 0
    assert stats.end_of_trip_dissolutions == 1


def test_members_with_one_exit_leaving_in_different_cycles_count_once():
    sim = Simulation(_config())
    vehicles = _place(sim, [(True, 2, 200, "end"), (True, 2, 199, "offramp"),
                            (True, 2, 198, "end"), (True, 2, 197, "offramp")])
    platoon = sim.controller.form(vehicles)
    sim.controller._leave_for_destination(platoon, [vehicles[1]])
    rear = vehicles[3].driver.platoon
    assert rear is not None and rear.split_destinations == {300}
    sim.controller._leave_for_destination(rear, [vehicles[3]])
    assert sim.controller.statistics().destination_splits == 1


def test_destination_splits_are_at_most_the_destinations_minus_one():
    sim = Simulation(_config("naive"))
    vehicles = _place(sim, [(True, 2, 200, "end"), (True, 2, 199, "offramp"),
                            (True, 2, 198, "end"), (True, 2, 197, "offramp"),
                            (True, 2, 196, "end")])
    platoon = sim.controller.form(vehicles)
    for member in (vehicles[1], vehicles[3]):
        if member.driver.platoon is not None:
            sim.controller._leave_for_destination(member.driver.platoon, [member])
    assert sim.controller.statistics().destination_splits == 1


def test_section_counts_are_per_lane_with_the_av_share():
    config = replace(_config(), sim_duration=40.0)
    sim = Simulation(config)
    platooned = _place(sim, [(True, 1, 60 - i, "end") for i in range(3)])
    lane_1 = platooned + _place(sim, [(False, 1, 40, "end")])
    lane_2 = _place(sim, [(True, 2, 60, "end"), (True, 2, 50, "end")])
    sim.controller.form(platooned)
    sim.run()
    counts = section_counts(lane_1 + lane_2, [100], [1, 2], 0.0)
    by_lane = {c.lane_idx: (c.vehicles, c.avs, c.units) for c in counts}
    assert by_lane == {1: (4, 3, 1), 2: (2, 2, 2)}
    assert counts[0].unit_size == 3 and counts[0].av_share == pytest.approx(0.75)
    assert pooled(counts) == (pytest.approx(5 / 3), pytest.approx(5 / 6))


def test_a_chain_break_carries_the_separated_destinations_to_the_rear_part():
    sim = Simulation(_config())
    vehicles = _place(sim, [(True, 2, 200, "end"), (True, 2, 199, "offramp"),
                            (True, 2, 198, "end"), (True, 2, 197, "offramp"),
                            (True, 2, 196, "end")])
    platoon = sim.controller.form(vehicles)
    sim.controller._leave_for_destination(platoon, [vehicles[1]])   # 300 separates: 1
    rear = vehicles[2].driver.platoon
    sim.controller._cut(rear, 1)                                     # a chain break
    rest = vehicles[3].driver.platoon
    assert rest is not None and rest.split_destinations == {300}
    sim.controller._leave_for_destination(rest, [vehicles[3]])       # 300 again: not counted
    assert sim.controller.statistics().destination_splits == 1       # D - 1 with D = 2


def test_formations_are_logged_by_size_and_destinations():
    sim = Simulation(_config("naive"))
    first = _place(sim, [(True, 1, 60, "end"), (True, 1, 59, "offramp"), (True, 1, 58, "end")])
    second = _place(sim, [(True, 2, 60, "end"), (True, 2, 59, "end")])
    sim.controller.form(first)
    sim.controller.form(second)
    assert sim.controller.statistics().formations_by_size_destinations == {"2,1": 1, "3,2": 1}
