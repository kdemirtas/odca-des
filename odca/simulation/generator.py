"""Vehicle generator: creates vehicles at origins according to OD flows."""

from __future__ import annotations

import logging
from dataclasses import dataclass, replace
from typing import List, Optional

import numpy as np
import simpy

from odca.entity.hdv import HDV
from odca.entity.av import AV
from odca.entity.av_controller import AVController
from odca.entity.driver import TraitSampler
from odca.entity.vehicle import Vehicle, VehicleType
from odca.infrastructure.freeway import Freeway
from odca.params import AutonomousDriverConfig, HumanDriverConfig, SimConfig, VehicleConfig

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class ODPair:
    """One entry of the demand table: vehicles per hour from `origin` to `destination`."""

    origin: str
    destination: str
    flow_rate: float  # veh/h


class VehicleGenerator:
    """Generates the vehicles of one OD pair, Poisson arrivals at its rate (D-2026-09-19-26)."""

    def __init__(
        self,
        env: simpy.Environment,
        freeway: Freeway,
        od: ODPair,
        sim: SimConfig,
        rng_gen: np.random.Generator,
        av_controller: AVController,
        # Per-source behavioral RNGs (shared across all vehicles)
        rng_slowdown: Optional[np.random.Generator] = None,
        rng_mlc: Optional[np.random.Generator] = None,
        rng_dlc: Optional[np.random.Generator] = None,
        traits: Optional[TraitSampler] = None,
    ):
        self.env = env
        self.freeway = freeway
        self.od = od
        self.hdv_vehicle: VehicleConfig = sim.hdv_vehicle
        self.hdv_driver: HumanDriverConfig = sim.hdv_driver
        self.av_vehicle: VehicleConfig = sim.av_vehicle
        self.av_driver: AutonomousDriverConfig = sim.av_driver
        self.av_penetration = sim.av_penetration
        self.sim_duration = sim.sim_duration
        self.rng_gen = rng_gen  # RNG for inter-arrival times and type selection
        self.av_controller = av_controller
        self.origin_cell = freeway.origin(od.origin).cell
        exit_to = freeway.destination(od.destination)
        self.destination_cell, self.destination_lane = exit_to.cell_idx, exit_to.lane

        # Per-source behavioral RNGs (shared across all vehicles)
        self.rng_slowdown = rng_slowdown
        self.rng_mlc = rng_mlc
        self.rng_dlc = rng_dlc

        self.traits = traits  # draws each human driver's own values (None: the means)

        # Derived
        self.mean_interval = 3600.0 / od.flow_rate  # seconds between vehicles

        # Tracking
        self.vehicles: List[Vehicle] = []
        self.num_generated = 0

    def _create_vehicle(self) -> Vehicle:
        """Create a single vehicle (AV or HDV)."""
        origin = self.origin_cell
        dest_cell, dest_lane = self.destination_cell, self.destination_lane

        if self.rng_gen.random() < self.av_penetration:
            veh = AV(
                env=self.env,
                rng_slowdown=self.rng_slowdown,
                rng_mlc=self.rng_mlc,
                rng_dlc=self.rng_dlc,
                vehicle=self.av_vehicle, driver=self.av_driver,
                origin_cell=origin,
                destination_cell_idx=dest_cell,
                destination_lane=dest_lane,
            )
        else:
            # Sample per-driver parameters for HDVs
            driver_params = (self.traits.driver_config(self.hdv_driver) if self.traits
                             else self.hdv_driver)
            veh = HDV(
                env=self.env,
                rng_slowdown=self.rng_slowdown,
                rng_mlc=self.rng_mlc,
                rng_dlc=self.rng_dlc,
                vehicle=self.hdv_vehicle, driver=driver_params,
                origin_cell=origin,
                destination_cell_idx=dest_cell,
                destination_lane=dest_lane,
            )
        return veh

    def run(self):
        """SimPy process: generate vehicles at mean_interval spacing."""
        logger.debug("Generator started: %s -> %s, rate=%.0f veh/h",
                     self.od.origin, self.od.destination, self.od.flow_rate)
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
                "t=%.2f  Generated %s (#%d for %s→cell %d, lane %s)",
                self.env.now, veh, self.num_generated,
                self.od.origin, veh.destination_cell_idx,
                veh.destination_lane,
            )
            self.env.process(veh.start())
