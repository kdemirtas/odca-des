"""Human-Driven Vehicle: concrete vehicle with HDV parameters."""

import numpy as np

from odca.entity.vehicle import Vehicle, VehicleType
from config import VehicleParams


class HDV(Vehicle):
    def __init__(self, env,
                 rng_slowdown: np.random.Generator,
                 rng_mlc: np.random.Generator,
                 rng_dlc: np.random.Generator,
                 params: VehicleParams,
                 origin_cell=None, destination_cell_idx=None, destination_lane=1):
        super().__init__(
            env=env,
            rng_slowdown=rng_slowdown,
            rng_mlc=rng_mlc,
            rng_dlc=rng_dlc,
            vtype=VehicleType.HDV,
            tau=params.tau,
            standstill_spacing=params.standstill_spacing,
            v_max=params.v_max,
            slowdown_prob=params.slowdown_prob,
            slowdown_delta=params.slowdown_delta,
            action_interval=params.action_interval,
            mlc_k=params.mlc_k,
            mlc_r0=params.mlc_r0,
            dlc_k=params.dlc_k,
            dlc_v0=params.dlc_v0,
            dlc_cooldown=params.dlc_cooldown,
            safety_gap_front=params.safety_gap_front,
            safety_gap_rear=params.safety_gap_rear,
            look_ahead=params.look_ahead,
            look_behind=params.look_behind,
            origin_cell=origin_cell,
            destination_cell_idx=destination_cell_idx,
            destination_lane=destination_lane,
        )
