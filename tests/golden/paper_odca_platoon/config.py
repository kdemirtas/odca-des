"""Parameter values for the platooning experiments.

The values live in YAML: vehicle and driver values are the odca package defaults
(`odca/configs/`), this paper's network, demand, run length and platoon controller parameters
are in `configs/`. This module loads them once and exposes them to the scripts.
Units: speed in cells/s, time in seconds, distance in cells (1 cell = CELL_LENGTH_M metres).
"""

from dataclasses import replace
from pathlib import Path

from odca.params import CELL_LENGTH_M, PlatoonConfig, SimConfig, validate

__all__ = [
    "CELL_LENGTH_M", "CONFIG_DIR", "SEEDS", "AV_DRIVER", "AV_VEHICLE", "PLATOON",
    "sim_config", "platoon_config",
]

CONFIG_DIR = Path(__file__).parent / "configs"

# every scenario runs these ten seeds
SEEDS = list(range(42, 52))

_DEFAULT: SimConfig = validate(SimConfig, CONFIG_DIR / "simulation.yaml")

AV_DRIVER = _DEFAULT.av_driver
AV_VEHICLE = _DEFAULT.av_vehicle
PLATOON: PlatoonConfig = validate(PlatoonConfig, CONFIG_DIR / "platoon.yaml")


def sim_config(**overrides) -> SimConfig:
    """The default run config with `overrides` applied.

    Args:
        **overrides: new values for any `SimConfig` field.
    """
    return replace(_DEFAULT, **overrides)


def platoon_config(strategy: str, **overrides) -> PlatoonConfig:
    """The paper's platoon controller parameters for `strategy`, with `overrides` applied.

    Args:
        strategy: naive, emp or dcp; any other name raises.
        **overrides: new values for any `PlatoonConfig` field.
    """
    return replace(PLATOON, strategy=strategy, **overrides)
