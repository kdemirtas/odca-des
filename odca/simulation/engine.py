"""Simulation engine: orchestrates the ODCA-DES simulation."""

from __future__ import annotations

import logging
from typing import Dict, List

import simpy

import numpy as np

from config import SimConfig, VehicleParams
from odca.infrastructure.freeway import Freeway
from odca.simulation.generator import VehicleGenerator
from odca.entity.hdv import HDV
from odca.entity.vehicle import Vehicle, VehicleType
from odca.entity.av_controller import AVController
from odca.rng import RNGRegistry

logger = logging.getLogger(__name__)


class Simulation:
    def __init__(self, config: SimConfig):
        self.config = config

        # Central RNG registry: all randomness flows from this master seed
        self.rng_registry = RNGRegistry(master_seed=config.seed)

        # Reset vehicle IDs
        Vehicle._id_counter = 0

        # Create SimPy environment
        self.env = simpy.Environment()

        # Build freeway
        net = config.network
        self.freeway = Freeway(
            env=self.env,
            num_lanes=net.num_lanes,
            num_cells=net.num_cells,
            speed_limit=net.speed_limit,
            onramp_cells=net.onramp_cells,
            offramp_cells=net.offramp_cells,
        )

        # Central AV controller
        self.av_controller = AVController(
            env=self.env,
            controller_dt=config.av_controller_dt,
        )

        # RNG streams: one per source of randomness (shared across all vehicles)
        # Runtime behavioral RNGs
        rng_slowdown = self.rng_registry.spawn("slowdown")
        rng_mlc = self.rng_registry.spawn("mlc")
        rng_dlc = self.rng_registry.spawn("dlc")
        # Per-driver heterogeneity RNGs (used at vehicle creation time)
        rng_tau = self.rng_registry.spawn("driver_tau")
        rng_action_interval = self.rng_registry.spawn("driver_action_interval")
        rng_slowdown_param = self.rng_registry.spawn("driver_slowdown_param")

        # Store RNGs for seeding initial vehicles
        self._rng_slowdown = rng_slowdown
        self._rng_mlc = rng_mlc
        self._rng_dlc = rng_dlc
        self._rng_tau = rng_tau
        self._rng_action_interval = rng_action_interval
        self._rng_slowdown_param = rng_slowdown_param

        # Vehicles placed at t=0 (initial condition)
        self._seeded_vehicles: List[Vehicle] = []

        self.generators: List[VehicleGenerator] = []
        for i, od in enumerate(config.od_flows):
            entry_lane, entry_cell = self._resolve_origin(od.origin_id)
            rng_gen = self.rng_registry.spawn(f"generator_{od.origin_id}_{i}")
            gen = VehicleGenerator(
                env=self.env,
                freeway=self.freeway,
                od_flow=od,
                hdv_params=config.hdv_params,
                av_params=config.av_params,
                av_penetration=config.av_penetration,
                sim_duration=config.sim_duration,
                rng_gen=rng_gen,
                av_controller=self.av_controller,
                entry_lane=entry_lane,
                entry_cell=entry_cell,
                rng_slowdown=rng_slowdown,
                rng_mlc=rng_mlc,
                rng_dlc=rng_dlc,
                rng_tau=rng_tau,
                rng_action_interval=rng_action_interval,
                rng_slowdown_param=rng_slowdown_param,
            )
            self.generators.append(gen)

    def _resolve_origin(self, origin_id: str):
        """Map origin ID to (lane_idx, cell_idx)."""
        if origin_id == "mainline":
            return 1, 0
        elif origin_id.startswith("mainline_lane_"):
            lane_idx = int(origin_id.split("_")[-1])
            return lane_idx, 0
        elif origin_id.startswith("onramp_"):
            ramp_num = int(origin_id.split("_")[1])
            ramp_cells = sorted(self.config.network.onramp_cells)
            cell_idx = ramp_cells[ramp_num - 1]
            return 1, cell_idx
        raise ValueError(f"Unknown origin: {origin_id}")

    def _sample_driver_params(self, params: VehicleParams) -> VehicleParams:
        """Sample per-driver heterogeneous parameters (same logic as generator)."""
        from dataclasses import replace
        overrides = {}
        if self._rng_tau is not None and params.tau_std > 0:
            mean, std = params.tau, params.tau_std
            sigma_ln2 = np.log(1 + (std / mean) ** 2)
            mu_ln = np.log(mean) - sigma_ln2 / 2
            val = self._rng_tau.lognormal(mu_ln, np.sqrt(sigma_ln2))
            overrides["tau"] = float(np.clip(val, 0.5, 3.0))
        if self._rng_action_interval is not None and params.action_interval_std > 0:
            mean, std = params.action_interval, params.action_interval_std
            sigma_ln2 = np.log(1 + (std / mean) ** 2)
            mu_ln = np.log(mean) - sigma_ln2 / 2
            val = self._rng_action_interval.lognormal(mu_ln, np.sqrt(sigma_ln2))
            overrides["action_interval"] = float(np.clip(val, 0.3, 3.0))
        if self._rng_slowdown_param is not None and params.slowdown_prob_std > 0:
            val = self._rng_slowdown_param.normal(params.slowdown_prob,
                                                   params.slowdown_prob_std)
            overrides["slowdown_prob"] = float(np.clip(val, 0.0, 1.0))
        if overrides:
            return replace(params, **overrides)
        return params

    def seed_vehicles(self, spacing: int, destination_cell_idx: int):
        """Place vehicles uniformly on all lanes at t=0.

        Parameters
        ----------
        spacing : int
            Cell spacing between vehicles (e.g. 15 cells ≈ free-flow
            density of ~8.9 veh/km at 7.5 m cells).
        destination_cell_idx : int
            Destination cell index for all seeded vehicles.
        """
        num_lanes = self.config.network.num_lanes
        num_cells = self.config.network.num_cells

        for lane_idx in range(1, num_lanes + 1):
            lane = self.freeway.lane(lane_idx)
            for cell_idx in range(0, num_cells, spacing):
                cell = lane.cells[cell_idx]
                if cell._blocked:
                    continue  # skip blocked cells (e.g. lane closure)
                driver_params = self._sample_driver_params(self.config.hdv_params)
                veh = HDV(
                    env=self.env,
                    rng_slowdown=self._rng_slowdown,
                    rng_mlc=self._rng_mlc,
                    rng_dlc=self._rng_dlc,
                    params=driver_params,
                    origin_cell=cell,
                    destination_cell_idx=destination_cell_idx,
                    destination_lane=lane_idx,
                )
                self._seeded_vehicles.append(veh)
                self.env.process(veh.start())

        logger.info(
            f"Seeded {len(self._seeded_vehicles)} vehicles "
            f"(spacing={spacing} cells, {num_lanes} lanes)"
        )

    def run(self) -> Dict:
        """Run the simulation and return results."""
        # Start AV controller
        self.env.process(self.av_controller.run())

        # Start all generators
        for gen in self.generators:
            self.env.process(gen.run())

        logger.info(f"Running simulation for {self.config.sim_duration}s...")
        self.env.run(until=self.config.sim_duration)
        logger.info(
            f"Simulation complete. t={self.env.now:.1f}s, "
            f"RNG streams spawned: {self.rng_registry.num_streams}"
        )

        return self._collect_results()

    def _collect_results(self) -> Dict:
        """Gather all vehicle trajectories and statistics."""
        all_vehicles: List[Vehicle] = []
        all_vehicles.extend(self._seeded_vehicles)
        for gen in self.generators:
            all_vehicles.extend(gen.vehicles)

        completed = [v for v in all_vehicles if v.time_exited is not None]
        active = [v for v in all_vehicles if v.active]

        total_generated = sum(g.num_generated for g in self.generators)

        # Aggregate event counters across all vehicles
        counters = {
            "lane_changes": sum(v.count_lane_changes for v in all_vehicles),
            "lc_failures": sum(v.count_lc_failures for v in all_vehicles),
            "slowdowns": sum(v.count_slowdowns for v in all_vehicles),
            "cf_evaluations": sum(v.count_cf_evaluations for v in all_vehicles),
            "av_controller_updates": self.av_controller.num_updates,
        }

        results = {
            "total_generated": total_generated,
            "total_completed": len(completed),
            "total_active_at_end": len(active),
            "vehicles": all_vehicles,
            "completed_vehicles": completed,
            "counters": counters,
            "config": self.config,
        }

        logger.info(
            f"Results: {total_generated} generated, "
            f"{len(completed)} completed, {len(active)} still active"
        )
        logger.info(
            f"Events: {counters['lane_changes']} lane changes, "
            f"{counters['lc_failures']} LC failures, "
            f"{counters['slowdowns']} slowdowns, "
            f"{counters['cf_evaluations']} car-following evals, "
            f"{counters['av_controller_updates']} AV controller updates"
        )
        return results
