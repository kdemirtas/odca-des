"""Platoon formation over time: a member that has split off for its exit is not grouped again
(D-2026-11-08-5), and a solo vehicle joins a platoon just ahead of or behind it, so a block
started from rest grows past pairs up to the size cap (D-2026-11-08-6)."""

from collections import Counter

import pytest

from odca.simulation.engine import Simulation
from test_platoon import _config, _place

# the paper-odca-platoon values that open the gap between the two rules: a member splits off
# 150 cells before its exit, a pair forms with 100 cells still to share
SPLIT_RULES = {"min_shared_path": 100, "split_lookahead": 150}


def _run(sim, until):
    """Run the controller (decisions and platoon management) up to `until`."""
    sim.env.process(sim.controller.run())
    sim.env.run(until=until)


def _platoon_sizes(controller):
    return Counter(p.size for p in controller.active_platoons())


def test_a_member_split_off_for_its_exit_is_not_grouped_again():
    sim = Simulation(_config("emp", **SPLIT_RULES))
    vehicles = _place(sim, [(True, 2, 103 - i, "offramp") for i in range(4)])
    controller = sim.controller
    controller.form(vehicles)
    formed_in_lane = []
    form = controller.form
    controller.form = lambda members: (formed_in_lane.append(members[0].cell.lane.idx),
                                       form(members))[1]
    _run(sim, 45.0)
    # one split at the look-ahead, none formed again outside the exit lane; at most one
    # platoon forms again in the exit lane, where nothing splits it
    assert all(vehicle.time_exited is not None for vehicle in vehicles)
    assert 2 not in formed_in_lane and len(formed_in_lane) <= 1
    assert controller.count_end_of_trip_dissolutions <= 2


def test_a_platoon_with_nothing_to_split_it_is_formed_once():
    sim = Simulation(_config("emp", **SPLIT_RULES))
    vehicles = _place(sim, [(True, 2, 103 - i, "end_lane_2") for i in range(4)])
    platoon = sim.controller.form(vehicles)
    _run(sim, 50.0)
    controller = sim.controller
    assert controller.count_formations == 1
    assert platoon.active and platoon.size == 4
    assert controller.count_end_of_trip_dissolutions == 0


@pytest.mark.parametrize("block,cap", [(3, 10), (5, 5), (8, 8), (10, 10)])
def test_a_block_started_from_rest_grows_to_one_platoon(block, cap):
    sim = Simulation(_config("emp", max_platoon_size=cap))
    vehicles = _place(sim, [(True, 1, 20 + block - 1 - i, "end") for i in range(block)])
    _run(sim, 20.0)
    platoon = vehicles[0].driver.platoon
    assert platoon is not None and platoon.members == vehicles
    assert _platoon_sizes(sim.controller) == Counter({block: 1})


def test_a_block_from_rest_longer_than_the_cap_is_platooned_within_the_cap():
    sim = Simulation(_config("emp", max_platoon_size=5))
    vehicles = _place(sim, [(True, 1, 26 - i, "end") for i in range(7)])
    _run(sim, 20.0)
    sizes = _platoon_sizes(sim.controller)
    assert all(v.driver.platoon is not None for v in vehicles)
    assert sum(size * n for size, n in sizes.items()) == 7 and max(sizes) <= 5
    assert sum(sizes.values()) == 2


def test_a_solo_vehicle_joins_at_the_tail_and_at_the_front():
    sim = Simulation(_config())
    front, a, b, rear = _place(sim, [(True, 1, 20 - i, "end") for i in range(4)])
    controller = sim.controller
    platoon = controller.form([a, b])
    controller.count_formations = 0
    controller._evaluate_joins([front, a, b, rear])
    assert platoon.members == [front, a, b, rear] and platoon.leader is front
    assert controller.count_joins == 2 and controller.count_formations == 0
    assert controller.statistics().total_joins == 2


def test_a_join_keeps_the_size_cap_and_the_strategy():
    sim = Simulation(_config("emp", max_platoon_size=3))
    vehicles = _place(sim, [(True, 1, 20 - i, "end") for i in range(4)])
    other = _place(sim, [(True, 1, 15, "offramp")])[0]
    controller = sim.controller
    platoon = controller.form(vehicles[1:4])
    controller._evaluate_joins(vehicles + [other])
    assert platoon.members == vehicles[1:4]        # full: the front one stays solo
    assert other.driver.platoon is None            # another exit under emp
    assert controller.count_joins == 0
