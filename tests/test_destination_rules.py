"""The two destination rules: no discretionary change away from the exit lane near the exit
(D-2026-10-03-5) and the stop line ahead of an off-ramp (D-2026-10-03-6). Off by default."""

import sys
from dataclasses import replace

import pytest

from odca.entity.vehicle import LaneChangeReason
from odca.params import DriverConfig, LogisticLaneChangeConfig
from odca.simulation.engine import Simulation

sys.path.insert(0, "tests/golden/paper_lc_logistic")
try:
    from config import sim_config
finally:
    sys.path.remove("tests/golden/paper_lc_logistic")
    for name in ("config",):
        sys.modules.pop(name, None)

NUM_CELLS = 800
FORCED = 0.05  # below this remaining ratio the mandatory curve is 1


def _run(keeps: bool, stops: bool, av_penetration: float):
    config = sim_config(sim_duration=600.0, warmup=0.0, seed=42, av_penetration=av_penetration)

    def with_rules(driver):
        return replace(driver, stops_for_offramp=stops,
                       lane_change=replace(driver.lane_change, dlc_keeps_destination=keeps))

    config = replace(config, hdv_driver=with_rules(config.hdv_driver),
                     av_driver=with_rules(config.av_driver))
    return Simulation(config).run().vehicles


def _offramp_vehicles(vehicles):
    return [v for v in vehicles if v.initial_distance is not None and v.time_exited is not None
            and v.origin_cell.idx + v.initial_distance < NUM_CELLS]


def _late_changes_away(vehicles):
    """Discretionary changes out of the exit lane inside the forced zone, by vehicles that
    reached their first destination (their leg is then the whole trip)."""
    found = 0
    for vehicle in vehicles:
        if vehicle.count_missed_exits or vehicle.initial_distance is None:
            continue
        destination = vehicle.origin_cell.idx + vehicle.initial_distance
        for record in vehicle.lane_changes:
            ratio = (destination - record.cell_idx) / vehicle.initial_distance
            if (record.reason is LaneChangeReason.DLC and ratio <= FORCED
                    and abs(record.to_lane - 1) > abs(record.from_lane - 1)
                    and destination < NUM_CELLS):
                found += 1
    return found


def test_both_rules_are_off_unless_a_config_turns_them_on():
    assert DriverConfig.__dataclass_fields__["stops_for_offramp"].default is False
    fields = LogisticLaneChangeConfig.__dataclass_fields__
    assert fields["dlc_keeps_destination"].default is False


def test_stop_line_lets_no_vehicle_pass_its_offramp_and_holds_none_for_good():
    # a mixed fleet, so human drivers (one decision a second) are held and released too
    # with the first rule on in both runs: few vehicles then reach the line, which is how
    # the two rules are meant to be used (the line alone costs delay behind held vehicles)
    without = _run(keeps=True, stops=False, av_penetration=0.5)
    assert sum(v.count_missed_exits > 0 for v in _offramp_vehicles(without)) > 0
    with_line = _run(keeps=True, stops=True, av_penetration=0.5)
    stopped = _offramp_vehicles(with_line)
    assert sum(v.count_missed_exits > 0 for v in stopped) == 0
    # nobody is left waiting at a line: as many off-ramp vehicles got out as without the
    # rule, within 5%, and so did the whole fleet
    assert len(stopped) >= 0.95 * len(_offramp_vehicles(without))
    done = sum(v.time_exited is not None for v in with_line)
    assert done >= 0.95 * sum(v.time_exited is not None for v in without)


def test_weight_is_one_minus_the_mandatory_curve_with_one_more_lane():
    from types import SimpleNamespace

    from odca.entity.driver import HumanDriver
    from odca.models.lane_changing.mandatory import mlc_probability

    def weight(lane, side_lane, destination_lane, ratio):
        vehicle = SimpleNamespace(destination_lane=destination_lane, destination_cell_idx=300,
                                  cell=SimpleNamespace(lane=SimpleNamespace(idx=lane)))
        driver = SimpleNamespace(vehicle=vehicle, _remaining_distance_ratio=lambda: ratio,
                                 lane_change=SimpleNamespace(mlc_k=8.0, mlc_r0=0.3))
        driver._lane_changes_to_destination = lambda: abs(lane - destination_lane)
        side = SimpleNamespace(lane=SimpleNamespace(idx=side_lane))
        return HumanDriver._keeps_destination_weight(driver, side)

    # in the exit lane, the lane beside leaves one change to make
    assert weight(1, 2, 1, 0.5) == pytest.approx(1 - mlc_probability(0.5, 1, 8.0, 0.3))
    # one lane short already, moving further away leaves two
    assert weight(2, 3, 1, 0.5) == pytest.approx(1 - mlc_probability(0.5, 2, 8.0, 0.3))
    assert weight(1, 2, 1, 0.04) == 0.0            # the forced zone rules it out
    assert weight(3, 2, 1, 0.04) == 1.0            # toward the destination: untouched
    assert weight(2, 3, None, 0.04) == 1.0         # no destination lane: untouched


def test_no_discretionary_change_away_from_the_exit_lane_in_the_forced_zone():
    assert _late_changes_away(_run(keeps=True, stops=False, av_penetration=0.0)) == 0
