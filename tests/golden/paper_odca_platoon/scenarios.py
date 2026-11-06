"""The scenario matrix, how one run is built and measured, and the run fingerprinted in odca-des.

`config.py`, `configs/` and this file are copied unchanged into
`odca-des/tests/golden/paper_odca_platoon/`, so `fingerprint.json` there proves the package
reproduces this paper's runs (odca-des:D-2026-11-05-2).
"""

import time
from dataclasses import asdict, replace
from typing import Optional

from config import platoon_config, sim_config
from odca.analysis.metrics import summary_statistics
from odca.params import SimConfig
from odca.platoon import pooled, section_counts
from odca.simulation.engine import Simulation
from odca.simulation.result import SimulationResult

QUICK_DURATION = 600.0   # s, the --quick runs of every script
QUICK_WARMUP = 60.0      # s

AV_PENETRATIONS = [0.3, 0.5, 0.7]
STRATEGY_LABELS = {"naive": "S1_naive", "emp": "S2_emp", "dcp": "S3_dcp"}

# (label, AV share, strategy or None), 13 scenarios in table order
SCENARIOS = [("B1_baseline", 0.0, None)]
SCENARIOS += [(f"B2_{int(av * 100)}av", av, None) for av in AV_PENETRATIONS]
for _strategy, _prefix in STRATEGY_LABELS.items():
    SCENARIOS += [(f"{_prefix}_{int(av * 100)}av", av, _strategy) for av in AV_PENETRATIONS]

# m-bar is counted at these sections (cells), the middle of the three stretches between ramps:
# on-ramp 1 (100) to off-ramp 1 (300), on-ramp 2 (400) to off-ramp 2 (550), off-ramp 2 to 3 (750)
MBAR_SECTIONS = [200, 475, 650]

# the demand sweep (D-2026-11-06-1): every OD pair times these factors, so 1,800, 2,100 and
# 2,400 veh/h per mainline lane; B2 and the platooning scenarios only
BASE_LANE_DEMAND = 1500.0   # veh/h per mainline lane in configs/demand.yaml
DEMAND_SCALES = [1.2, 1.4, 1.6]
DEMAND_SWEEP_SCENARIOS = [s for s in SCENARIOS if s[1] > 0]

GOLDEN_SCENARIO = "S3_dcp_70av"
GOLDEN_SEED = 42


def scenario_config(av_penetration: float, strategy: Optional[str], seed: int,
                    quick: bool = False, demand_scale: float = 1.0,
                    **platoon_overrides) -> SimConfig:
    """The run config of one scenario replication.

    Args:
        av_penetration: AV share of the demand.
        strategy: naive, emp or dcp; None runs no platooning.
        seed: the run's master seed.
        quick: the short run (QUICK_DURATION, QUICK_WARMUP).
        demand_scale: every OD pair of the demand times this factor (D-2026-11-06-1).
        **platoon_overrides: new values for `PlatoonConfig` fields (sensitivity sweeps).
    """
    config = sim_config(av_penetration=av_penetration, seed=seed)
    if demand_scale != 1.0:
        demand = {origin: {dest: rate * demand_scale for dest, rate in pairs.items()}
                  for origin, pairs in config.demand.items()}
        config = replace(config, demand=demand)
    if strategy is not None:
        controller = replace(config.controller,
                             platoon=platoon_config(strategy, **platoon_overrides))
        config = replace(config, controller=controller)
    if quick:
        config = replace(config, sim_duration=QUICK_DURATION, warmup=QUICK_WARMUP)
    return config


def measure(result: SimulationResult) -> dict:
    """The summary statistics of one run, over every vehicle, plus m-bar and alpha (AVs per AV
    unit, and AVs per vehicle, crossing the MBAR_SECTIONS after the warm-up: pooled, per lane,
    and the raw counts per section and lane) and the platoon statistics.

    Args:
        result: what `Simulation.run` returned.
    """
    config = result.config
    stats = summary_statistics(result.vehicles, warmup=config.warmup,
                               sim_duration=config.sim_duration)
    lanes = range(1, config.network.num_lanes + 1)
    counts = section_counts(result.vehicles, MBAR_SECTIONS, lanes, config.warmup)
    # m-bar as the paper defines it (Sec. 4.3): the section count, pooled over sections and lanes
    stats["avg_av_unit_size"], stats["av_share"] = pooled(counts)
    stats["av_unit_size_by_lane"] = {
        str(lane): pooled(c for c in counts if c.lane_idx == lane)[0] for lane in lanes}
    stats["av_share_by_lane"] = {
        str(lane): pooled(c for c in counts if c.lane_idx == lane)[1] for lane in lanes}
    stats["section_counts"] = [asdict(c) for c in counts]
    stats["counters"] = asdict(result.counters)
    stats["platoon_stats"] = asdict(result.platoons) if result.platoons is not None else {}
    return stats


def run_scenario(label: str, av_penetration: float, strategy: Optional[str], seed: int,
                 quick: bool = False, demand_scale: float = 1.0,
                 **platoon_overrides) -> dict:
    """Run one scenario replication and return its result row.

    Args:
        label: the scenario label, written into the row.
        av_penetration: AV share of the demand.
        strategy: naive, emp or dcp; None runs no platooning.
        seed: the run's master seed.
        quick: the short run.
        demand_scale: every OD pair of the demand times this factor (D-2026-11-06-1).
        **platoon_overrides: new values for `PlatoonConfig` fields (sensitivity sweeps).
    """
    config = scenario_config(av_penetration, strategy, seed, quick, demand_scale,
                             **platoon_overrides)
    started = time.time()
    stats = measure(Simulation(config).run())
    stats["wall_time_s"] = round(time.time() - started, 2)
    stats["av_penetration"] = av_penetration
    stats["strategy"] = strategy or "none"
    stats["seed"] = seed
    stats["label"] = label
    stats["demand_scale"] = demand_scale
    stats["lane_demand"] = BASE_LANE_DEMAND * demand_scale
    return stats


def golden_runs():
    """(run_id, callable returning (stats, counters)) for every fingerprinted run."""
    label, av_penetration, strategy = next(s for s in SCENARIOS if s[0] == GOLDEN_SCENARIO)
    config = scenario_config(av_penetration, strategy, GOLDEN_SEED, quick=True)

    def run():
        result = Simulation(config).run()
        stats = measure(result)
        counters = stats.pop("counters")
        platoon_stats = stats.pop("platoon_stats")
        stats.update({f"platoon_{k}": v for k, v in platoon_stats.items()})
        return stats, counters

    return [(f"{label}_seed{GOLDEN_SEED}", run)]
