"""Vehicle factory: the one place a vehicle is built with its driver.

D-2026-09-19-24, D-2026-09-19-30.
"""

from __future__ import annotations

from typing import Optional

import simpy

from odca.entity.controller import AutonomousController
from odca.entity.driver import AutonomousDriver, DriverStreams, HumanDriver, TraitSampler
from odca.entity.vehicle import Vehicle
from odca.infrastructure.cell import Cell
from odca.infrastructure.freeway import Destination
from odca.params import SimConfig


class VehicleFactory:
    """Builds human-driven and autonomous vehicles from a run's configs."""

    def __init__(self, env: simpy.Environment, sim: SimConfig, streams: DriverStreams,
                 traits: TraitSampler, controller: AutonomousController):
        """A factory for one run.

        Args:
            env: the SimPy environment.
            sim: the run config (vehicle and driver configs of both kinds).
            streams: the decision streams every driver shares.
            traits: draws each human driver's own values.
            controller: decides for the autonomous drivers.
        """
        self.env = env
        self.sim = sim
        self.streams = streams
        self.traits = traits
        self.controller = controller

    def build(self, autonomous: bool, origin_cell: Cell,
              destination: Optional[Destination]) -> Vehicle:
        """A new vehicle and its driver; a human driver's traits are drawn here.

        Args:
            autonomous: an autonomous vehicle, else a human-driven one.
            origin_cell: the road cell it enters at.
            destination: where it leaves.
        """
        sim = self.sim
        if autonomous:
            driver = AutonomousDriver(sim.av_driver, self.streams, self.controller)
            return Vehicle(self.env, sim.av_vehicle, driver, origin_cell, destination)
        driver = HumanDriver(sim.hdv_driver, self.streams, self.traits.draw(sim.hdv_driver))
        return Vehicle(self.env, sim.hdv_vehicle, driver, origin_cell, destination)
