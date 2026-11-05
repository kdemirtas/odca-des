"""Train platooning of autonomous vehicles, off unless `ControllerConfig.platoon` is set
(D-2026-11-05-1)."""

from odca.platoon.controller import PlatoonController, PlatoonStatistics, PlatoonStrategy
from odca.platoon.driver import PlatoonDriver
from odca.platoon.measures import (
    SectionCount, av_unit_size_at, count_av_units, pooled, section_counts,
)
from odca.platoon.platoon import Platoon

__all__ = ["Platoon", "PlatoonController", "PlatoonDriver", "PlatoonStatistics",
           "PlatoonStrategy", "SectionCount", "av_unit_size_at", "count_av_units", "pooled",
           "section_counts"]
