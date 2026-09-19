"""Central AV Controller: coordinates all autonomous vehicles.

Unlike HDVs, which each run their own independent driver process,
AVs are coordinated by a single central controller that fires every
controller_dt seconds. This reflects the connected nature of AVs
(V2V/V2I communication) and is computationally efficient: one SimPy
event per cycle instead of N_AV events.

The controller evaluates speed and direction for each active AV
in a single pass. The movement process remains per-vehicle — each AV
still independently acquires and releases cell resources.
"""

from __future__ import annotations

import logging
from typing import List

import simpy

from odca.entity.vehicle import Vehicle, VehicleType

logger = logging.getLogger(__name__)


class AVController:
    """Central controller for all autonomous vehicles."""

    def __init__(self, env: simpy.Environment, controller_dt: float = 0.1):
        self.env = env
        self.controller_dt = controller_dt
        self._vehicles: List[Vehicle] = []
        self.num_updates = 0

    def register(self, vehicle: Vehicle):
        """Register an AV to be managed by this controller.

        An AV decides at the controller's rate, so a blocked AV also retries its move every
        controller_dt, not at the 0.5 s action interval of its parameters (D-2026-09-19-19).
        """
        vehicle.action_interval = self.controller_dt
        self._vehicles.append(vehicle)

    @property
    def active_vehicles(self) -> List[Vehicle]:
        return [v for v in self._vehicles if v.active]

    def run(self):
        """SimPy process: periodically evaluate all active AVs."""
        logger.debug("AV Controller started (dt=%.2fs)", self.controller_dt)
        while True:
            yield self.env.timeout(self.controller_dt)

            active = self.active_vehicles
            if not active:
                continue

            for av in active:
                av._evaluate_speed()
                av._evaluate_direction()

            self.num_updates += 1
            logger.debug(
                "t=%.2f  AV Controller update #%d: %d active AVs",
                self.env.now, self.num_updates, len(active),
            )
