"""Vehicle generator: creates vehicles at origins according to OD flows."""

from __future__ import annotations

import logging
from dataclasses import replace
from typing import List, Optional

import numpy as np
import simpy

from config import VehicleParams, ODFlow
from odca.entity.hdv import HDV
from odca.entity.av import AV
from odca.entity.av_controller import AVController
from odca.entity.vehicle import Vehicle, VehicleType
from odca.infrastructure.freeway import Freeway

logger = logging.getLogger(__name__)


class VehicleGenerator:
    """Generates vehicles for a single OD pair."""

    def __init__(
        self,
        env: simpy.Environment,
        freeway: Freeway,
        od_flow: ODFlow,
        hdv_params: VehicleParams,
        av_params: VehicleParams,
        av_penetration: float,
        sim_duration: float,
        rng_gen: np.random.Generator,
        av_controller: AVController,
        entry_lane: int = 1,
        entry_cell: int = 0,
        # Per-source behavioral RNGs (shared across all vehicles)
        rng_slowdown: Optional[np.random.Generator] = None,
        rng_mlc: Optional[np.random.Generator] = None,
        rng_dlc: Optional[np.random.Generator] = None,
        # Per-driver heterogeneity RNGs (used at vehicle creation time)
        rng_tau: Optional[np.random.Generator] = None,
        rng_action_interval: Optional[np.random.Generator] = None,
        rng_slowdown_param: Optional[np.random.Generator] = None,
    ):
        self.env = env
        self.freeway = freeway
        self.od_flow = od_flow
        self.hdv_params = hdv_params
        self.av_params = av_params
        self.av_penetration = av_penetration
        self.sim_duration = sim_duration
        self.rng_gen = rng_gen  # RNG for inter-arrival times and type selection
        self.av_controller = av_controller
        self.entry_lane = entry_lane
        self.entry_cell = entry_cell

        # Per-source behavioral RNGs (shared across all vehicles)
        self.rng_slowdown = rng_slowdown
        self.rng_mlc = rng_mlc
        self.rng_dlc = rng_dlc

        # Per-driver heterogeneity RNGs (creation-time sampling)
        self.rng_tau = rng_tau
        self.rng_action_interval = rng_action_interval
        self.rng_slowdown_param = rng_slowdown_param

        # Derived
        self.mean_interval = 3600.0 / od_flow.flow_rate  # seconds between vehicles

        # Tracking
        self.vehicles: List[Vehicle] = []
        self.num_generated = 0

    def _sample_destination(self) -> tuple:
        """Sample a (destination_cell, destination_lane) for the next vehicle.

        If the ODFlow has a destinations distribution, sample from it.
        Otherwise, use the legacy single destination_cell.
        """
        if self.od_flow.destinations:
            cells = [d[0] for d in self.od_flow.destinations]
            probs = [d[1] for d in self.od_flow.destinations]
            dest_cell = self.rng_gen.choice(cells, p=probs)
        else:
            dest_cell = self.od_flow.destination_cell

        # Destination lane: 1 (rightmost) for off-ramps, entry lane for end
        if dest_cell in self.freeway.offramp_cells:
            dest_lane = 1
        else:
            dest_lane = self.entry_lane
        return int(dest_cell), dest_lane

    def _sample_driver_params(self, params: VehicleParams) -> VehicleParams:
        """Sample per-driver behavioral parameters for HDVs.

        Uses log-normal for tau and action_interval (always positive,
        right-skewed for occasional inattentive drivers). Uses truncated
        normal for slowdown_prob (bounded to [0, 1]).
        """
        overrides = {}

        if self.rng_tau is not None and params.tau_std > 0:
            # Log-normal: compute mu_ln, sigma_ln from desired mean and std
            mean, std = params.tau, params.tau_std
            sigma_ln2 = np.log(1 + (std / mean) ** 2)
            mu_ln = np.log(mean) - sigma_ln2 / 2
            val = self.rng_tau.lognormal(mu_ln, np.sqrt(sigma_ln2))
            overrides["tau"] = float(np.clip(val, 0.5, 3.0))

        if self.rng_action_interval is not None and params.action_interval_std > 0:
            mean, std = params.action_interval, params.action_interval_std
            sigma_ln2 = np.log(1 + (std / mean) ** 2)
            mu_ln = np.log(mean) - sigma_ln2 / 2
            val = self.rng_action_interval.lognormal(mu_ln, np.sqrt(sigma_ln2))
            overrides["action_interval"] = float(np.clip(val, 0.3, 3.0))

        if self.rng_slowdown_param is not None and params.slowdown_prob_std > 0:
            val = self.rng_slowdown_param.normal(params.slowdown_prob,
                                                  params.slowdown_prob_std)
            overrides["slowdown_prob"] = float(np.clip(val, 0.0, 1.0))

        if overrides:
            return replace(params, **overrides)
        return params

    def _create_vehicle(self) -> Vehicle:
        """Create a single vehicle (AV or HDV)."""
        origin = self.freeway.lane(self.entry_lane).cells[self.entry_cell]
        dest_cell, dest_lane = self._sample_destination()

        if self.rng_gen.random() < self.av_penetration:
            veh = AV(
                env=self.env,
                rng_slowdown=self.rng_slowdown,
                rng_mlc=self.rng_mlc,
                rng_dlc=self.rng_dlc,
                params=self.av_params,
                origin_cell=origin,
                destination_cell_idx=dest_cell,
                destination_lane=dest_lane,
            )
        else:
            # Sample per-driver parameters for HDVs
            driver_params = self._sample_driver_params(self.hdv_params)
            veh = HDV(
                env=self.env,
                rng_slowdown=self.rng_slowdown,
                rng_mlc=self.rng_mlc,
                rng_dlc=self.rng_dlc,
                params=driver_params,
                origin_cell=origin,
                destination_cell_idx=dest_cell,
                destination_lane=dest_lane,
            )
        return veh

    def run(self):
        """SimPy process: generate vehicles at mean_interval spacing."""
        dest_info = (self.od_flow.destinations if self.od_flow.destinations
                     else f"cell {self.od_flow.destination_cell}")
        logger.debug(
            "Generator started: %s → %s, rate=%.0f veh/h",
            self.od_flow.origin_id, dest_info,
            self.od_flow.flow_rate,
        )
        while self.env.now < self.sim_duration:
            # Exponential inter-arrival using numpy RNG
            interval = self.rng_gen.exponential(self.mean_interval)
            yield self.env.timeout(interval)

            veh = self._create_vehicle()
            self.vehicles.append(veh)
            self.num_generated += 1

            # Register AVs with central controller
            if veh.vtype == VehicleType.AV:
                self.av_controller.register(veh)

            logger.debug(
                "t=%.2f  Generated %s (#%d for %s→cell %d, lane %d)",
                self.env.now, veh, self.num_generated,
                self.od_flow.origin_id, veh.destination_cell_idx,
                veh.destination_lane,
            )
            self.env.process(veh.start())
