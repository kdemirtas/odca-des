"""The two road invariants of ARCHITECTURE.md: one vehicle per cell, and the headway floor."""

import sys
from collections import defaultdict
from dataclasses import replace

import pytest
import simpy

from odca.entity.driver import DriverStreams, DriverTraits, HumanDriver
from odca.entity.vehicle import LaneChangeReason, Vehicle
from odca.infrastructure.freeway import Freeway
from odca.params import NetworkConfig
from odca.rng import RNGRegistry
from odca.simulation.engine import Simulation

sys.path.insert(0, "tests/golden/paper_odca_des")
try:
    from config import HDV_DRIVER, HDV_VEHICLE, sim_config
finally:
    sys.path.remove("tests/golden/paper_odca_des")
    sys.modules.pop("config", None)


def _stays_by_cell(vehicles):
    """(arrival, departure) of every completed passage, by (lane, cell)."""
    stays = defaultdict(list)
    for vehicle in vehicles:
        records = vehicle.trajectory
        for here, after in zip(records, records[1:]):
            stays[(here.lane_idx, here.cell_idx)].append((here.time, after.time))
    return stays


def test_no_vehicle_arrives_in_a_cell_another_is_still_in():
    result = Simulation(sim_config(seed=1, sim_duration=300.0, warmup=30.0)).run()
    stays = _stays_by_cell(result.vehicles)
    assert sum(len(spans) for spans in stays.values()) > 200_000
    for spans in stays.values():
        spans.sort()
        for (_, left), (next_arrived, _) in zip(spans, spans[1:]):
            assert next_arrived >= left - 1e-9


class FixedSpeedDriver(HumanDriver):
    """Holds one speed and its lane, whatever is ahead."""

    fixed_speed = 2.0

    def decide(self):
        self.vehicle.set_target_speed(self.fixed_speed)


class CrawlingDriver(FixedSpeedDriver):
    """Crosses a cell in 5 s, longer than tau."""

    fixed_speed = 0.2


def test_every_lane_change_is_logged_with_its_reason():
    result = Simulation(sim_config(av_penetration=0.5, seed=1, sim_duration=120.0,
                                   warmup=0.0)).run()
    assert result.counters.lane_changes > 0
    for vehicle in result.vehicles:
        assert len(vehicle.lane_changes) == vehicle.count_lane_changes
        for record in vehicle.lane_changes:
            assert isinstance(record.reason, LaneChangeReason)
            assert abs(record.to_lane - record.from_lane) == 1


def test_no_vehicle_arrives_behind_a_crawling_vehicle_before_it_has_left():
    env = simpy.Environment()
    freeway = Freeway(env, NetworkConfig.corridor(1, 12, 5.2))
    streams = DriverStreams.spawn(RNGRegistry(master_seed=1))
    traits = DriverTraits.exact(HDV_DRIVER)
    end = freeway.destination("end_lane_1")
    crawler = Vehicle(env, HDV_VEHICLE, CrawlingDriver(HDV_DRIVER, streams, traits),
                      freeway.cell(1, 0), end)
    follower = Vehicle(env, HDV_VEHICLE, FixedSpeedDriver(HDV_DRIVER, streams, traits),
                       freeway.cell(1, 0), end)
    env.process(crawler.start())
    env.process(follower.start())
    env.run(until=200)
    assert 1 / CrawlingDriver.fixed_speed > traits.tau
    arrivals = {record.cell_idx: record.time for record in follower.trajectory}
    crossed = 0
    for here, after in zip(crawler.trajectory, crawler.trajectory[1:]):
        if here.cell_idx in arrivals and here.cell_idx > 0:
            assert arrivals[here.cell_idx] >= after.time
            crossed += 1
    assert crossed >= 8


def test_headway_on_the_road_is_never_below_tau_plus_the_crossing_time():
    driver = replace(HDV_DRIVER, tau_std=0.0, action_interval_std=0.0, slowdown_prob_std=0.0,
                     slowdown_prob=0.0)
    config = sim_config(network=NetworkConfig.corridor(1, 100, HDV_VEHICLE.v_max),
                        demand={"mainline_lane_1": {"end_lane_1": 3000.0}}, hdv_driver=driver,
                        av_penetration=0.0, sim_duration=600.0, warmup=30.0, seed=1)
    result = Simulation(config).run()
    floor = driver.tau + HDV_VEHICLE.standstill_spacing / HDV_VEHICLE.v_max
    assert 3600 / floor == pytest.approx(2127, abs=0.5)
    smallest = float("inf")
    for (_, cell_idx), spans in _stays_by_cell(result.vehicles).items():
        if cell_idx == 0:
            continue  # a vehicle is placed in its origin cell, it does not cross into it
        arrivals = sorted(arrived for arrived, _ in spans)
        smallest = min([smallest] + [b - a for a, b in zip(arrivals, arrivals[1:])])
    assert smallest == pytest.approx(floor, abs=1e-9)


def test_two_crawling_vehicles_keep_the_newell_headway():
    env = simpy.Environment()
    freeway = Freeway(env, NetworkConfig.corridor(1, 12, 5.2))
    streams = DriverStreams.spawn(RNGRegistry(master_seed=1))
    traits = DriverTraits.exact(HDV_DRIVER)
    end = freeway.destination("end_lane_1")
    pair = [Vehicle(env, HDV_VEHICLE, CrawlingDriver(HDV_DRIVER, streams, traits),
                    freeway.cell(1, 0), end) for _ in range(2)]
    for vehicle in pair:
        env.process(vehicle.start())
    env.run(until=200)
    leader = {record.cell_idx: record.time for record in pair[0].trajectory}
    follower = {record.cell_idx: record.time for record in pair[1].trajectory}
    newell = traits.tau + 1 / CrawlingDriver.fixed_speed
    assert 1 / CrawlingDriver.fixed_speed > traits.tau
    for cell_idx in range(2, 10):
        assert follower[cell_idx] - leader[cell_idx] == pytest.approx(newell, abs=1e-9)
