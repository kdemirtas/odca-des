"""Human-driven vehicle."""

import numpy as np

from odca.entity.vehicle import Vehicle, VehicleType, config_kwargs
from odca.params import DriverConfig, VehicleConfig


class HDV(Vehicle):
    """A vehicle of type HDV, built from its vehicle and driver configs."""

    def __init__(self, env,
                 rng_slowdown: np.random.Generator,
                 rng_mlc: np.random.Generator,
                 rng_dlc: np.random.Generator,
                 vehicle: VehicleConfig, driver: DriverConfig,
                 origin_cell=None, destination_cell_idx=None,
                 destination_lane=1):
        super().__init__(
            env=env, rng_slowdown=rng_slowdown, rng_mlc=rng_mlc, rng_dlc=rng_dlc,
            vtype=VehicleType.HDV, **config_kwargs(vehicle, driver),
            origin_cell=origin_cell, destination_cell_idx=destination_cell_idx,
            destination_lane=destination_lane,
        )
