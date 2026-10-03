"""The driver split (D-2026-09-19-24): factory, link, controller, a driver subclass."""

import sys
from dataclasses import dataclass, replace

import pytest
import simpy

from odca.entity.driver import DriverStreams, DriverTraits, HumanDriver
from odca.entity.vehicle import Direction, LaneChangeReason, Vehicle
from odca.infrastructure.freeway import Freeway
from odca.params import BaseLaneChangeConfig, NetworkConfig, family_member
from odca.rng import RNGRegistry
from odca.simulation.engine import Simulation

sys.path.insert(0, "tests/golden/paper_odca_des")
try:
    from config import HDV_DRIVER, HDV_VEHICLE, sim_config
finally:
    sys.path.remove("tests/golden/paper_odca_des")
    sys.modules.pop("config", None)


def test_factory_links_both_kinds():
    sim = Simulation(sim_config())
    cell, end = sim.freeway.cell(1, 0), sim.freeway.destination("end_lane_1")
    human = sim.factory.build(False, cell, end)
    robot = sim.factory.build(True, cell, end)
    assert (human.kind, robot.kind) == ("human", "autonomous")
    assert human.driver.vehicle is human and robot.driver.vehicle is robot
    assert robot.driver.action_interval == sim.cfg.controller.dt
    assert robot.driver in sim.controller._drivers
    assert human.driver not in sim.controller._drivers
    assert human.driver.tau != HDV_DRIVER.tau  # drawn, not the mean


def test_each_run_numbers_its_own_vehicles_from_zero():
    first, second = Simulation(sim_config()), Simulation(sim_config())
    cell, end = first.freeway.cell(1, 0), first.freeway.destination("end_lane_1")
    other_cell, other_end = second.freeway.cell(1, 0), second.freeway.destination("end_lane_1")
    ids = [first.factory.build(False, cell, end).id, second.factory.build(True, other_cell,
                                                                         other_end).id,
           first.factory.build(True, cell, end).id, second.factory.build(False, other_cell,
                                                                        other_end).id]
    assert ids == [0, 0, 1, 1]


def test_counters_split_between_vehicle_and_driver_sum_in_results():
    sim = Simulation(sim_config(sim_duration=400.0, seed=2))
    results = sim.run()
    vehicles = results.vehicles
    assert results.counters.lc_patience_failures == sum(
        v.count_lc_patience_failures for v in vehicles)
    assert results.counters.gap_rejections == sum(
        v.driver.count_gap_rejections for v in vehicles)
    assert results.counters.lc_failures == (results.counters.lc_patience_failures
                                            + results.counters.gap_rejections)
    assert results.counters.speed_evaluations == sum(
        v.driver.count_speed_evaluations for v in vehicles)


class SteadyDriver(HumanDriver):
    """Keeps 2 cells/s and its lane."""

    def decide(self):
        self.vehicle.set_target_speed(2.0)


def test_a_driver_subclass_drives_a_vehicle():
    env = simpy.Environment()
    freeway = Freeway(env, NetworkConfig.corridor(1, 40, 5.2))
    streams = DriverStreams.spawn(RNGRegistry(master_seed=1))
    driver = SteadyDriver(HDV_DRIVER, streams, DriverTraits.exact(HDV_DRIVER))
    vehicle = Vehicle(env, HDV_VEHICLE, driver, freeway.cell(1, 0),
                      freeway.destination("end_lane_1"))
    env.process(vehicle.start())
    env.run(until=60)
    speeds = {r.speed for r in vehicle.trajectory[1:]}
    assert speeds == {2.0}
    assert vehicle.time_exited is not None and 18.0 <= vehicle.time_exited <= 20.0


class OneLeftDriver(SteadyDriver):
    """Asks for one lane change to the left, once."""

    def decide(self):
        super().decide()
        if self.vehicle.count_lane_changes == 0:
            self.vehicle.request_direction(Direction.LEFT, LaneChangeReason.DLC)


def test_one_request_makes_one_lane_change():
    env = simpy.Environment()
    freeway = Freeway(env, NetworkConfig.corridor(3, 40, 5.2))
    streams = DriverStreams.spawn(RNGRegistry(master_seed=1))
    driver = OneLeftDriver(HDV_DRIVER, streams, DriverTraits.exact(HDV_DRIVER))
    vehicle = Vehicle(env, HDV_VEHICLE, driver, freeway.cell(1, 0), freeway.destination("end"))
    env.process(vehicle.start())
    env.run(until=60)
    assert vehicle.count_lane_changes == 1
    assert vehicle.trajectory[-1].lane_idx == 2
    (record,) = vehicle.lane_changes
    assert (record.from_lane, record.to_lane, record.reason) == (1, 2, LaneChangeReason.DLC)


def test_lane_change_request_needs_a_reason():
    env = simpy.Environment()
    freeway = Freeway(env, NetworkConfig.corridor(2, 40, 5.2))
    streams = DriverStreams.spawn(RNGRegistry(master_seed=1))
    driver = SteadyDriver(HDV_DRIVER, streams, DriverTraits.exact(HDV_DRIVER))
    vehicle = Vehicle(env, HDV_VEHICLE, driver, freeway.cell(1, 0), freeway.destination("end"))
    with pytest.raises(ValueError):
        vehicle.request_direction(Direction.LEFT)


def _gap_accepted(look_ahead, look_behind):
    """Whether a stopped vehicle accepts a gap with a fast follower one cell behind it."""
    env = simpy.Environment()
    freeway = Freeway(env, NetworkConfig.corridor(2, 40, 5.2))
    streams = DriverStreams.spawn(RNGRegistry(master_seed=1))
    cfg = replace(HDV_DRIVER, look_ahead=look_ahead, look_behind=look_behind)

    def placed(lane, cell_idx, speed):
        vehicle = Vehicle(env, HDV_VEHICLE, HumanDriver(cfg, streams, DriverTraits.exact(cfg)),
                          freeway.cell(lane, cell_idx))
        vehicle.cell = freeway.cell(lane, cell_idx)
        vehicle.cell.vehicle = vehicle
        vehicle.speed = speed
        return vehicle

    subject = placed(1, 20, 0.0)
    placed(2, 20, HDV_VEHICLE.v_max)  # the follower, one cell behind the target
    return subject.driver.accepts_gap(freeway.cell(2, 21))


def test_the_rear_gap_scan_reads_look_behind():
    assert not _gap_accepted(look_ahead=1, look_behind=10)  # seen behind, gap refused
    assert _gap_accepted(look_ahead=10, look_behind=0)      # not looked for, gap accepted


def test_result_carries_the_config_it_ran_with(tmp_path):
    from odca.params import SimConfig, validate
    config = sim_config(sim_duration=120.0, seed=4)
    result = Simulation(config).run()
    assert result.config == config
    path = tmp_path / "run.yaml"
    path.write_text(result.config_yaml())
    assert validate(SimConfig, path) == config
    assert result.num_completed + result.num_active_at_end <= len(result.vehicles)


def test_a_lane_change_model_picks_its_driver_class():
    @family_member("keep_lane")
    @dataclass(frozen=True, slots=True, kw_only=True)
    class KeepLaneConfig(BaseLaneChangeConfig):
        model: str = "keep_lane"

    class KeepLaneDriver(HumanDriver):
        lane_change_config = KeepLaneConfig

        def evaluate_direction(self):
            self.vehicle.request_direction(Direction.FORWARD)

    try:
        assert HumanDriver.class_for(HDV_DRIVER) is HumanDriver
        base = dict(safety_gap_front=2.0, safety_gap_rear=2.0, dlc_cooldown=10.0)
        keep = replace(HDV_DRIVER, lane_change=KeepLaneConfig(**base))
        assert HumanDriver.class_for(keep) is KeepLaneDriver
        result = Simulation(sim_config(hdv_driver=keep, seed=1, sim_duration=60.0,
                                       warmup=0.0)).run()
        assert result.vehicles and result.counters.lane_changes == 0
        assert all(type(v.driver) is KeepLaneDriver for v in result.vehicles)

        @dataclass(frozen=True, slots=True, kw_only=True)
        class UnclaimedConfig(BaseLaneChangeConfig):
            model: str = "unclaimed"

        with pytest.raises(ValueError):
            HumanDriver.class_for(replace(HDV_DRIVER, lane_change=UnclaimedConfig(**base)))
    finally:
        HumanDriver._by_lane_change.pop(KeepLaneConfig, None)
        BaseLaneChangeConfig.members.pop("keep_lane", None)
