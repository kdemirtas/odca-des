"""The driver split (D-2026-09-19-24): factory, link, controller, a driver subclass."""

import sys

import simpy

from odca.entity.driver import DriverStreams, DriverTraits, HumanDriver
from odca.entity.vehicle import Direction, Vehicle
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


def test_counters_split_between_vehicle_and_driver_sum_in_results():
    sim = Simulation(sim_config(sim_duration=400.0, seed=2))
    results = sim.run()
    vehicles = results.vehicles
    assert results.counters.lc_failures == sum(
        v.count_lc_failures + v.driver.count_gap_rejections for v in vehicles)
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
            self.vehicle.request_direction(Direction.LEFT)


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


def test_result_carries_the_config_it_ran_with(tmp_path):
    from odca.params import SimConfig, validate
    config = sim_config(sim_duration=120.0, seed=4)
    result = Simulation(config).run()
    assert result.config == config
    path = tmp_path / "run.yaml"
    path.write_text(result.config_yaml())
    assert validate(SimConfig, path) == config
    assert result.num_completed + result.num_active_at_end <= len(result.vehicles)
