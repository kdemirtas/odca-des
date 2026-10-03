"""A vehicle longer than one cell holds every cell from its front to its rear (D-2026-10-03-8)."""

import sys
from dataclasses import replace

import pytest
import simpy

from odca.entity.driver import DriverStreams, DriverTraits, HumanDriver
from odca.entity.vehicle import Direction, LaneChangeReason, Vehicle
from odca.infrastructure.freeway import Freeway
from odca.models.car_following import newell
from odca.params import NetworkConfig, VehicleConfig
from odca.rng import RNGRegistry

sys.path.insert(0, "tests/golden/paper_odca_des")
try:
    from config import HDV_DRIVER, HDV_VEHICLE
finally:
    sys.path.remove("tests/golden/paper_odca_des")
    sys.modules.pop("config", None)

BUS = replace(HDV_VEHICLE, length=3)


class FixedSpeedDriver(HumanDriver):
    """Holds one speed and its lane, whatever is ahead."""

    fixed_speed = 1.0

    def decide(self):
        self.vehicle.set_target_speed(self.fixed_speed)


class FasterDriver(FixedSpeedDriver):
    """Drives at twice the speed of the vehicle ahead of it in these tests."""

    fixed_speed = 2.0


class LeftThenRightDriver(FixedSpeedDriver):
    """Asks for the left lane from cell 5 on, then for the right lane as soon as it is there."""

    changes_back = True

    def decide(self):
        vehicle = self.vehicle
        vehicle.set_target_speed(self.fixed_speed)
        if vehicle.cell.lane.idx == 1 and vehicle.cell.idx >= 5 and not vehicle.lane_changes:
            vehicle.request_direction(Direction.LEFT, LaneChangeReason.DLC)
        elif (self.changes_back and vehicle.cell.lane.idx == 2
              and len(vehicle.lane_changes) == 1):
            vehicle.request_direction(Direction.RIGHT, LaneChangeReason.DLC)


class LeftDriver(LeftThenRightDriver):
    """Asks for the left lane from cell 5 on and stays there."""

    changes_back = False


def _road(num_lanes, num_cells):
    env = simpy.Environment()
    freeway = Freeway(env, NetworkConfig.corridor(num_lanes, num_cells, 5.2))
    streams = DriverStreams.spawn(RNGRegistry(master_seed=1))
    return env, freeway, streams, DriverTraits.exact(HDV_DRIVER)


def _cells_of(vehicle, freeway):
    """(lane, cell) of every cell that is marked as holding `vehicle`."""
    return sorted((lane.idx, cell.idx) for lane in freeway.lanes for cell in lane.cells
                  if cell.vehicle is vehicle)


def _watch(env, vehicle, freeway, snapshots):
    """Record the cells `vehicle` is in whenever they change."""
    while True:
        cells = _cells_of(vehicle, freeway)
        if not snapshots or snapshots[-1] != cells:
            snapshots.append(cells)
        yield env.timeout(0.01)


def test_length_is_a_whole_number_of_cells():
    assert VehicleConfig(v_max=5.2, standstill_spacing=1.0).length == 1
    for bad in (0, -1, 1.5, True):
        with pytest.raises(ValueError):
            replace(HDV_VEHICLE, length=bad)


def test_a_three_cell_vehicle_holds_three_cells_and_leaves_none_behind():
    env, freeway, streams, traits = _road(1, 20)
    bus = Vehicle(env, BUS, FixedSpeedDriver(HDV_DRIVER, streams, traits),
                  freeway.cell(1, 0), freeway.destination("end_lane_1"))
    snapshots = []
    env.process(bus.start())
    env.process(_watch(env, bus, freeway, snapshots))
    env.run(until=100)
    # it comes onto the road one cell at a time, then holds three consecutive cells
    assert snapshots[:4] == [[], [(1, 0)], [(1, 0), (1, 1)], [(1, 0), (1, 1), (1, 2)]]
    on_the_road = [cells for cells in snapshots if len(cells) == 3]
    assert len(on_the_road) >= 15
    for cells in on_the_road:
        indices = [idx for _, idx in cells]
        assert indices == list(range(indices[0], indices[0] + 3))
    assert max(len(cells) for cells in snapshots) == 3
    # once it has driven out, no cell is marked or locked
    assert bus.time_exited is not None
    assert snapshots[-1] == []
    assert not any(cell.is_occupied for lane in freeway.lanes for cell in lane.cells)


def test_no_vehicle_arrives_in_a_cell_the_rear_of_a_long_vehicle_is_still_in():
    env, freeway, streams, traits = _road(1, 30)
    end = freeway.destination("end_lane_1")
    bus = Vehicle(env, BUS, FixedSpeedDriver(HDV_DRIVER, streams, traits),
                  freeway.cell(1, 0), end)
    car = Vehicle(env, HDV_VEHICLE, FasterDriver(HDV_DRIVER, streams, traits),
                  freeway.cell(1, 0), end)
    env.process(bus.start())
    env.process(car.start())
    env.run(until=200)
    front_arrived = {record.cell_idx: record.time for record in bus.trajectory}
    car_arrived = {record.cell_idx: record.time for record in car.trajectory}
    checked = 0
    for cell_idx, arrived in car_arrived.items():
        rear_left = front_arrived.get(cell_idx + BUS.length)
        if cell_idx > 0 and rear_left is not None:
            # the rear leaves a cell when the front arrives three cells further on
            assert arrived >= rear_left - 1e-9
            checked += 1
    assert checked >= 20


def test_a_lane_change_needs_its_front_gap_to_the_rear_of_a_long_leader():
    env, freeway, streams, traits = _road(2, 40)
    bus = Vehicle(env, BUS, FixedSpeedDriver(HDV_DRIVER, streams, traits),
                  freeway.cell(1, 0), freeway.destination("end_lane_1"))
    env.process(bus.start())
    env.run(until=10)
    lane_1 = freeway.cell(1, 0).lane
    assert bus.cells_behind_front_in(lane_1) == 2
    rear = bus.cell.idx - 2
    car = Vehicle(env, HDV_VEHICLE, HumanDriver(HDV_DRIVER, streams, traits),
                  freeway.cell(2, 0), freeway.destination("end"))
    car.speed, bus.speed = HDV_VEHICLE.v_max, 0.0  # closing at top speed: the full safety gap
    needed = HDV_DRIVER.lane_change.safety_gap_front
    assert needed == 2.0
    # one cell short of the gap to the rear, although the gap to the front would do
    assert bus.cell.idx - (rear - 1) >= needed
    assert not car.driver.accepts_gap(freeway.cell(1, rear - 1))
    assert car.driver.accepts_gap(freeway.cell(1, rear - 2))


def test_the_body_follows_the_front_through_a_lane_change():
    env, freeway, streams, traits = _road(2, 30)
    bus = Vehicle(env, BUS, LeftThenRightDriver(HDV_DRIVER, streams, traits),
                  freeway.cell(1, 0), freeway.destination("end"))
    snapshots = []
    env.process(bus.start())
    env.process(_watch(env, bus, freeway, snapshots))
    env.run(until=100)
    assert bus.count_lane_changes == 2
    first, second = bus.lane_changes
    assert (first.from_lane, first.to_lane) == (1, 2)
    k = first.cell_idx  # the front left lane 1 at cell k for lane 2, cell k + 1
    expected = [
        [(1, k - 2), (1, k - 1), (1, k)],
        [(1, k - 1), (1, k), (2, k + 1)],
        [(1, k), (2, k + 1), (2, k + 2)],
        [(2, k + 1), (2, k + 2), (2, k + 3)],
    ]
    start = snapshots.index(expected[0])
    assert snapshots[start:start + 4] == expected
    # asked for at once, the change back waits until the whole body is in lane 2
    assert (second.from_lane, second.to_lane) == (2, 1)
    assert second.cell_idx >= k + 3


def test_car_following_reads_the_spacing_to_the_rear_of_a_long_leader():
    env, freeway, streams, traits = _road(1, 60)
    end = freeway.destination("end_lane_1")
    bus = Vehicle(env, BUS, FixedSpeedDriver(HDV_DRIVER, streams, traits),
                  freeway.cell(1, 0), end)
    car = Vehicle(env, HDV_VEHICLE, HumanDriver(HDV_DRIVER, streams, traits),
                  freeway.cell(1, 0), end)
    env.process(bus.start())
    env.process(car.start())
    env.run(until=20)
    assert bus.cells_behind_front_in(bus.cell.lane) == 2 and car.active
    to_the_rear = bus.fractional_position - 2 - car.fractional_position
    assert to_the_rear > 0
    car.driver._speed_for_leader(bus, HDV_VEHICLE.v_max)
    expected = newell.desired_speed(
        current_spacing=to_the_rear, leader_speed=bus.speed, tau=car.driver.tau,
        d=HDV_VEHICLE.standstill_spacing, v_max=HDV_VEHICLE.v_max)
    assert expected > 0
    assert car.speed == pytest.approx(expected)
    to_the_front = newell.desired_speed(
        current_spacing=to_the_rear + 2, leader_speed=bus.speed, tau=car.driver.tau,
        d=HDV_VEHICLE.standstill_spacing, v_max=HDV_VEHICLE.v_max)
    assert car.speed < to_the_front



def test_a_follower_in_the_new_lane_sees_only_the_cells_the_leader_has_there():
    env, freeway, streams, traits = _road(2, 30)
    bus = Vehicle(env, BUS, LeftDriver(HDV_DRIVER, streams, traits),
                  freeway.cell(1, 0), freeway.destination("end"))
    reach = []

    def watch():
        lane_1, lane_2 = freeway.cell(1, 0).lane, freeway.cell(2, 0).lane
        while True:
            if bus.cell is not None and len(bus.lane_changes) == 1:
                cells = _cells_of(bus, freeway)
                reach.append((cells, bus.cell.lane.idx, bus.cells_behind_front_in(lane_1),
                              bus.cells_behind_front_in(lane_2)))
            yield env.timeout(0.01)

    env.process(bus.start())
    env.process(watch())
    env.run(until=100)
    k = bus.lane_changes[0].cell_idx
    by_cells = {tuple(cells): rest for cells, *rest in reach}
    # front just in lane 2: nothing behind it there, two cells behind it in lane 1
    assert by_cells[((1, k - 1), (1, k), (2, k + 1))] == [2, 2, 0]
    assert by_cells[((1, k), (2, k + 1), (2, k + 2))] == [2, 2, 1]
    assert by_cells[((2, k + 1), (2, k + 2), (2, k + 3))] == [2, 0, 2]


def test_a_long_vehicle_leaves_through_a_throttled_destination():
    env, freeway, streams, traits = _road(1, 20)
    exits = [exit_cell for cell in freeway.lanes[0].cells for exit_cell in cell.exits]
    assert exits
    for exit_cell in exits:
        exit_cell.speed_limit = 0.5
    bus = Vehicle(env, BUS, FixedSpeedDriver(HDV_DRIVER, streams, traits),
                  freeway.cell(1, 0), freeway.destination("end_lane_1"))
    env.process(bus.start())
    env.run(until=200)
    assert bus.time_exited is not None
    assert _cells_of(bus, freeway) == []
    assert not any(cell.is_occupied for cell in freeway.lanes[0].cells)
    assert not any(exit_cell.is_occupied for exit_cell in exits)


def test_a_long_vehicle_is_refused_with_the_offramp_stop_line():
    env, freeway, streams, traits = _road(2, 20)
    driver = HumanDriver(replace(HDV_DRIVER, stops_for_offramp=True), streams, traits)
    with pytest.raises(ValueError, match="stops_for_offramp"):
        Vehicle(env, BUS, driver, freeway.cell(1, 0), freeway.destination("end"))
    # a one-cell vehicle runs with it as before
    Vehicle(env, HDV_VEHICLE, HumanDriver(replace(HDV_DRIVER, stops_for_offramp=True),
                                          streams, traits),
            freeway.cell(1, 0), freeway.destination("end"))
