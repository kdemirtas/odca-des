"""How one run of this paper is built and measured, and the short runs fingerprinted in odca-des.

`config.py`, `configs/` and this file are copied unchanged into
`odca-des/tests/golden/paper_lc_logistic/`, so `fingerprint.json` there proves the package
reproduces this paper's runs (paper-lc-logistic:D-2026-10-03-3).
"""

from collections import Counter
from dataclasses import asdict

from config import sim_config
from odca.analysis.metrics import summary_statistics
from odca.entity.vehicle import LaneChangeReason
from odca.params import SimConfig
from odca.simulation.engine import Simulation

GOLDEN_SEED = 42
GOLDEN_DURATION = 300.0   # s
GOLDEN_WARMUP = 30.0      # s
GOLDEN_SCENARIOS = [
    ("logistic_hdv", 0.0),
    ("logistic_mixed50", 0.5),
]


def lane_change_totals(vehicles, warmup: float) -> dict:
    """Lane changes made after the warm-up, in total and by kind.

    Args:
        vehicles: every vehicle of the run.
        warmup: seconds before counting starts.

    Returns:
        `total_lc`, `total_mlc` (blockage and destination) and `total_dlc`.
    """
    counts = Counter(r.reason for v in vehicles for r in v.lane_changes if r.time >= warmup)
    mlc = counts[LaneChangeReason.MLC_BLOCKAGE] + counts[LaneChangeReason.MLC_DESTINATION]
    dlc = counts[LaneChangeReason.DLC]
    if mlc + dlc != sum(counts.values()):
        raise ValueError(f"lane changes without a known reason: {dict(counts)}")
    return {"total_lc": mlc + dlc, "total_mlc": mlc, "total_dlc": dlc}


def run(config: SimConfig):
    """Run `config` once.

    Args:
        config: the run config.

    Returns:
        (stats, counters): the summary statistics over every vehicle, with the lane-change
        totals and the run's identifying values added, and the event counters.
    """
    result = Simulation(config).run()
    stats = summary_statistics(result.vehicles, warmup=config.warmup,
                               sim_duration=config.sim_duration)
    stats.update(lane_change_totals(result.vehicles, config.warmup))
    stats["av_penetration"] = config.av_penetration
    stats["seed"] = config.seed
    return stats, asdict(result.counters)


def golden_runs():
    """(run_id, callable returning (stats, counters)) for every fingerprinted run."""
    runs = []
    for label, av_penetration in GOLDEN_SCENARIOS:
        config = sim_config(av_penetration=av_penetration, seed=GOLDEN_SEED,
                            sim_duration=GOLDEN_DURATION, warmup=GOLDEN_WARMUP)
        runs.append((f"{label}_seed{GOLDEN_SEED}", lambda c=config: run(c)))
    return runs
