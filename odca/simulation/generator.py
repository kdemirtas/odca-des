"""Vehicle generator: creates vehicles at origins according to OD flows."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import List

import numpy as np
import simpy

from odca.entity.vehicle import Vehicle
from odca.infrastructure.freeway import Freeway
from odca.params import SimConfig
from odca.simulation.factory import VehicleFactory

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class ODPair:
    """One entry of the demand table: vehicles per hour from `origin` to `destination`."""

    origin: str
    destination: str
    flow_rate: float  # veh/h


class VehicleGenerator:
    """Generates the vehicles of one OD pair, Poisson arrivals at its rate (D-2026-09-19-26)."""

    def __init__(self, env: simpy.Environment, freeway: Freeway, od: ODPair, sim: SimConfig,
                 rng_gen: np.random.Generator, factory: VehicleFactory):
        """A generator for one OD pair.

        Args:
            env: the SimPy environment.
            freeway: the road, to find the origin and destination by name.
            od: the pair and its rate.
            sim: the run config (AV share, duration).
            rng_gen: this pair's stream: arrival gaps and the AV draw.
            factory: builds each vehicle with its driver.
        """
        self.env = env
        self.od = od
        self.av_penetration = sim.av_penetration
        self.sim_duration = sim.sim_duration
        self.rng_gen = rng_gen
        self.factory = factory
        self.origin_cell = freeway.origin(od.origin).cell
        self.destination = freeway.destination(od.destination)
        self.mean_interval = 3600.0 / od.flow_rate  # seconds between vehicles

        self.vehicles: List[Vehicle] = []
        self.num_generated = 0

    def run(self):
        """SimPy process: generate vehicles at exponential gaps until the run ends."""
        logger.debug("Generator started: %s -> %s, rate=%.0f veh/h",
                     self.od.origin, self.od.destination, self.od.flow_rate)
        while self.env.now < self.sim_duration:
            interval = self.rng_gen.exponential(self.mean_interval)
            yield self.env.timeout(interval)

            autonomous = self.rng_gen.random() < self.av_penetration
            veh = self.factory.build(autonomous, self.origin_cell, self.destination)
            self.vehicles.append(veh)
            self.num_generated += 1

            logger.debug(
                "t=%.2f  Generated %s (#%d for %s→cell %d, lane %s)",
                self.env.now, veh, self.num_generated,
                self.od.origin, veh.destination_cell_idx,
                veh.destination_lane,
            )
            self.env.process(veh.start())
