"""Parameter values for the lane-changing experiments (paper-lc-logistic:D-2026-10-03-3).

The values live in YAML: the vehicle and driver values are the odca package defaults
(`odca/configs/`), this paper's network, demand and run length in `configs/`. This module
loads them once and exposes them to the scripts.
Units: speed in cells/s, time in seconds, distance in cells (1 cell = CELL_LENGTH_M metres).
"""

from dataclasses import replace
from pathlib import Path

from odca.params import CELL_LENGTH_M, SimConfig, validate

__all__ = [
    "CELL_LENGTH_M", "CONFIG_DIR", "SEEDS", "HDV_DRIVER", "AV_DRIVER", "NETWORK", "DEMAND",
    "sim_config",
]

CONFIG_DIR = Path(__file__).parent / "configs"

# every experiment point runs these ten seeds (paper-lc-logistic:D-2026-10-03-4)
SEEDS = list(range(42, 52))

_DEFAULT: SimConfig = validate(SimConfig, CONFIG_DIR / "simulation.yaml")

HDV_DRIVER = _DEFAULT.hdv_driver
AV_DRIVER = _DEFAULT.av_driver
NETWORK = _DEFAULT.network
DEMAND = _DEFAULT.demand


def sim_config(**overrides) -> SimConfig:
    """The default run config with `overrides` applied.

    Args:
        **overrides: new values for any `SimConfig` field.
    """
    return replace(_DEFAULT, **overrides)
