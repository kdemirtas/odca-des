"""Parameter values for the ODCA-DES experiments.

The values live in YAML: the vehicle and driver calibration is the odca package default
(`odca/configs/`), this paper's S1 network, demand and run in `configs/` (D-2026-09-19-23).
This module loads them once and exposes them to the scripts.
Units: speed in cells/s, time in seconds, distance in cells (1 cell = CELL_LENGTH_M metres).
"""

from dataclasses import replace
from pathlib import Path

from odca.params import CELL_LENGTH_M, SimConfig, validate

__all__ = [
    "CELL_LENGTH_M", "CONFIG_DIR", "HDV_VEHICLE", "HDV_DRIVER", "AV_VEHICLE", "AV_DRIVER",
    "S1_NETWORK", "S1_DEMAND", "sim_config",
]

CONFIG_DIR = Path(__file__).parent / "configs"

_S1: SimConfig = validate(SimConfig, CONFIG_DIR / "simulation.yaml")

HDV_VEHICLE = _S1.hdv_vehicle
HDV_DRIVER = _S1.hdv_driver
AV_VEHICLE = _S1.av_vehicle
AV_DRIVER = _S1.av_driver
S1_NETWORK = _S1.network
S1_DEMAND = _S1.demand


def sim_config(**overrides) -> SimConfig:
    """The S1 run config with `overrides` applied.

    Args:
        **overrides: new values for any `SimConfig` field.
    """
    return replace(_S1, **overrides)
