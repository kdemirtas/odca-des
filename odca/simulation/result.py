"""One run's result: the resolved config, every vehicle and the run counters.

D-2026-09-19-32.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List

from omegaconf import OmegaConf

from odca.entity.vehicle import Vehicle
from odca.params import SimConfig


@dataclass(frozen=True, slots=True)
class RunCounters:
    """Event counts summed over a run's vehicles and its controller."""

    lane_changes: int
    lc_patience_failures: int   # lateral requests not granted within the patience
    gap_rejections: int         # target cells the driver judged unsafe
    slowdowns: int
    cf_evaluations: int
    speed_evaluations: int
    missed_exits: int
    av_controller_updates: int
    simpy_events: int

    @classmethod
    def of(cls, vehicles: List[Vehicle], controller_updates: int, events: int) -> RunCounters:
        """The counters of `vehicles` and their drivers.

        Args:
            vehicles: every vehicle of the run.
            controller_updates: cycles the autonomous controller decided in.
            events: SimPy events processed.
        """
        return cls(
            lane_changes=sum(v.count_lane_changes for v in vehicles),
            lc_patience_failures=sum(v.count_lc_patience_failures for v in vehicles),
            gap_rejections=sum(v.driver.count_gap_rejections for v in vehicles),
            slowdowns=sum(v.driver.count_slowdowns for v in vehicles),
            cf_evaluations=sum(v.driver.count_cf_evaluations for v in vehicles),
            speed_evaluations=sum(v.driver.count_speed_evaluations for v in vehicles),
            missed_exits=sum(v.count_missed_exits for v in vehicles),
            av_controller_updates=controller_updates,
            simpy_events=events,
        )

    @property
    def lc_failures(self) -> int:
        """Lane-change attempts that did not happen, either way (D-2026-09-20-12)."""
        return self.lc_patience_failures + self.gap_rejections


@dataclass(frozen=True)
class SimulationResult:
    """What one run produced; `config` is the validated config it ran with."""

    config: SimConfig
    vehicles: List[Vehicle]   # placed at t=0 first, then generated, in order
    num_generated: int        # by the generators (vehicles placed at t=0 not counted)
    counters: RunCounters

    @property
    def completed_vehicles(self) -> List[Vehicle]:
        """The vehicles that left the road before the run ended."""
        return [v for v in self.vehicles if v.time_exited is not None]

    @property
    def num_completed(self) -> int:
        """How many vehicles left the road."""
        return len(self.completed_vehicles)

    @property
    def num_active_at_end(self) -> int:
        """How many vehicles were still on the road when the run ended."""
        return sum(1 for v in self.vehicles if v.active)

    def config_yaml(self) -> str:
        """The config as YAML; `Simulation(validate(SimConfig, path))` reruns it."""
        return OmegaConf.to_yaml(OmegaConf.structured(self.config))
