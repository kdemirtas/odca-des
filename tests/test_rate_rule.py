"""The lane-change rate rule: what the curves are a probability per (D-2026-10-03-4)."""

import sys
from dataclasses import replace

import pytest

from odca.models.lane_changing.rate import exposures, probability_over
from odca.params import RATE_RULES
from odca.simulation.engine import Simulation

sys.path.insert(0, "tests/golden/paper_odca_des")
try:
    from config import AV_DRIVER, sim_config
finally:
    sys.path.remove("tests/golden/paper_odca_des")
    for name in ("config",):
        sys.modules.pop(name, None)


def test_exposure_per_rule():
    # 0.1 s since the last evaluation, 0.52 cells driven = 0.1 reference distances
    assert exposures("distance", 0.1, 0.1) == (0.1, 0.1)
    assert exposures("distance", 2.0, 0.1) == (0.1, 2.0)   # crawling: little distance, much time
    assert exposures("second", 2.0, 0.1) == (2.0, 2.0)
    assert exposures("evaluation", 2.0, 0.1) == (1.0, 1.0)
    with pytest.raises(ValueError):
        exposures("per_decision", 1.0, 1.0)


def test_per_evaluation_uses_the_curve_value_as_it_is():
    assert probability_over(0.3, exposures("evaluation", 0.1, 0.1)[0]) == pytest.approx(0.3)
    # ten evaluations a second under the distance rule add up to the per-reference value
    stay = (1 - probability_over(0.3, exposures("distance", 0.1, 0.1)[0])) ** 10
    assert 1 - stay == pytest.approx(0.3)


def test_default_rule_and_unknown_rule():
    assert AV_DRIVER.lane_change.rate_rule == "distance"
    assert RATE_RULES == ("distance", "second", "evaluation")
    with pytest.raises(ValueError):
        replace(AV_DRIVER.lane_change, rate_rule="per_decision")


def _lane_changes(rule):
    lane_change = replace(AV_DRIVER.lane_change, dlc_enabled=True, rate_rule=rule)
    config = sim_config(av_driver=replace(AV_DRIVER, lane_change=lane_change),
                        av_penetration=1.0, seed=1, sim_duration=120.0, warmup=0.0)
    return Simulation(config).run().counters.lane_changes


def test_a_10_hz_driver_changes_lanes_more_often_per_evaluation():
    assert _lane_changes("evaluation") > 1.2 * _lane_changes("distance")
