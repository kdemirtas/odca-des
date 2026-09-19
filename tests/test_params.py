"""Config validation: types checked, unknown keys refused, subclasses kept (D-2026-09-19-23)."""

import pytest
from omegaconf.errors import ConfigKeyError, MissingMandatoryValue, ValidationError

from odca.entity.controller import AutonomousController
from odca.params import (
    BaseLaneChangeConfig,
    ControllerConfig,
    HumanDriverConfig,
    LogisticLaneChangeConfig,
    validate,
)

LANE_CHANGE = LogisticLaneChangeConfig(mlc_k=8.0, mlc_r0=0.3, dlc_k=3.0, dlc_v0=1.0,
                                       dlc_cooldown=10.0, safety_gap_front=2.0,
                                       safety_gap_rear=2.0)
DRIVER = dict(tau=1.5, action_interval=1.0, slowdown_prob=0.15, slowdown_delta=0.5,
              look_ahead=10, look_behind=10, lane_change=LANE_CHANGE)


def test_mapping_becomes_the_frozen_dataclass():
    cfg = validate(HumanDriverConfig, {**DRIVER, "tau": 2})
    assert isinstance(cfg, HumanDriverConfig) and cfg.tau == 2.0
    with pytest.raises(AttributeError):
        cfg.tau = 3.0


def test_subclass_in_a_base_typed_field_is_kept():
    cfg = validate(HumanDriverConfig, HumanDriverConfig(**DRIVER))
    assert isinstance(cfg.lane_change, LogisticLaneChangeConfig)
    assert isinstance(cfg.lane_change, BaseLaneChangeConfig)


@pytest.mark.parametrize("bad, error", [
    ({**DRIVER, "tau": "fast"}, ValidationError),
    ({**DRIVER, "reaction": 1.0}, ConfigKeyError),
    ({k: v for k, v in DRIVER.items() if k != "tau"}, MissingMandatoryValue),
])
def test_bad_config_is_refused(bad, error):
    with pytest.raises(error):
        validate(HumanDriverConfig, bad)


def test_yaml_file_and_save_round_trip(tmp_path):
    path = tmp_path / "controller.yaml"
    path.write_text("dt: 0.2\n")
    controller = AutonomousController.from_config(path, env=None)
    assert controller.cfg == ControllerConfig(dt=0.2)
    saved = tmp_path / "saved.yaml"
    saved.write_text(controller.save_config())
    assert validate(ControllerConfig, saved) == controller.cfg


def test_yaml_names_the_lane_change_model(tmp_path):
    lane_change = ("lane_change: {model: logistic, mlc_k: 8, mlc_r0: 0.3, dlc_k: 3, dlc_v0: 1,"
                   " dlc_cooldown: 10, safety_gap_front: 2, safety_gap_rear: 2}\n")
    path = tmp_path / "driver.yaml"
    path.write_text("tau: 1.5\naction_interval: 1\nslowdown_prob: 0.15\nslowdown_delta: 0.5\n"
                    "look_ahead: 10\nlook_behind: 10\n" + lane_change)
    assert validate(HumanDriverConfig, path) == HumanDriverConfig(**DRIVER)


@pytest.mark.parametrize("model", [None, "gipps"])
def test_unknown_or_missing_model_is_refused(model):
    lane_change = {"safety_gap_front": 2, "safety_gap_rear": 2, "dlc_cooldown": 10}
    if model:
        lane_change["model"] = model
    with pytest.raises(ValueError, match="logistic"):
        validate(HumanDriverConfig, {**DRIVER, "lane_change": lane_change})


def test_full_run_config_survives_a_yaml_round_trip(tmp_path):
    import sys
    sys.path.insert(0, "tests/golden/paper_odca_des")
    try:
        from config import sim_config
    finally:
        sys.path.remove("tests/golden/paper_odca_des")
        sys.modules.pop("config", None)
    from odca.simulation.engine import Simulation
    original = sim_config(av_penetration=0.3, seed=7)
    path = tmp_path / "run.yaml"
    path.write_text(Simulation(original).save_config())
    assert validate(type(original), path) == original


def test_package_defaults_load_and_a_scenario_overrides_them(tmp_path):
    default = validate(HumanDriverConfig, "odca://hdv_driver.yaml")
    path = tmp_path / "driver.yaml"
    path.write_text("_base_: odca://hdv_driver.yaml\naction_interval: 0.5\n"
                    "lane_change: {dlc_cooldown: 5}\n")
    changed = validate(HumanDriverConfig, path)
    assert changed.action_interval == 0.5 and changed.lane_change.dlc_cooldown == 5.0
    assert changed.tau == default.tau
    assert changed.lane_change.mlc_k == default.lane_change.mlc_k


@pytest.mark.parametrize("demand, message", [
    ({"mainline_lane_1": {"cell_500": 100.0}}, "unknown destination"),
    ({"onramp_9": {"end": 100.0}}, "unknown origin"),
    ({"mainline_lane_1": {"end_lane_1": 0.0}}, "veh/h"),
])
def test_bad_demand_is_refused(demand, message):
    import sys
    sys.path.insert(0, "tests/golden/paper_odca_des")
    try:
        from config import sim_config
    finally:
        sys.path.remove("tests/golden/paper_odca_des")
        sys.modules.pop("config", None)
    from odca.simulation.engine import Simulation
    with pytest.raises(ValueError, match=message):
        Simulation(sim_config(demand=demand))


def test_whole_numbers_are_accepted_in_float_tables():
    from odca.params import NetworkConfig, SimConfig
    network = NetworkConfig.corridor(1, 50, 5.2)
    cfg = validate(SimConfig, {"network": network, "demand": {"mainline_lane_1": {"end": 400}},
                               "hdv_vehicle": "odca://hdv_vehicle.yaml",
                               "hdv_driver": "odca://hdv_driver.yaml",
                               "av_vehicle": "odca://av_vehicle.yaml",
                               "av_driver": "odca://av_driver.yaml"})
    assert cfg.demand == {"mainline_lane_1": {"end": 400.0}}
