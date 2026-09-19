"""Autonomous controller: decides for every autonomous driver (D-2026-09-19-24, D-2026-09-19-30).

Human drivers each run their own process; autonomous drivers are decided for by one controller
every `dt` seconds, which reflects connected vehicles (V2V/V2I) and costs one SimPy event per
cycle instead of one per vehicle. Each vehicle still moves in its own process.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, List

import simpy

from odca.params import ConfigMixin, ControllerConfig

if TYPE_CHECKING:
    from odca.entity.driver import AutonomousDriver

logger = logging.getLogger(__name__)


class AutonomousController(ConfigMixin):
    """Central controller for all autonomous drivers."""

    Config = ControllerConfig

    def __init__(self, cfg: ControllerConfig, env: simpy.Environment):
        """Controller deciding for every registered driver each `cfg.dt` seconds.

        Args:
            cfg: the controller config.
            env: the SimPy environment it runs in.
        """
        self.cfg = cfg
        self.env = env
        self._drivers: List[AutonomousDriver] = []
        self.num_updates = 0

    def register(self, driver: AutonomousDriver):
        """Decide for `driver` from the next cycle on.

        Args:
            driver: a new autonomous driver.
        """
        self._drivers.append(driver)

    @property
    def active_drivers(self) -> List[AutonomousDriver]:
        """The registered drivers whose vehicle is on the road."""
        return [d for d in self._drivers if d.vehicle.active]

    def run(self):
        """SimPy process: decide for every active driver each `dt`."""
        logger.debug("Autonomous controller started (dt=%.2fs)", self.cfg.dt)
        while True:
            yield self.env.timeout(self.cfg.dt)

            active = self.active_drivers
            if not active:
                continue

            for driver in active:
                driver.decide()

            self.num_updates += 1
            logger.debug(
                "t=%.2f  controller update #%d: %d active drivers",
                self.env.now, self.num_updates, len(active),
            )
