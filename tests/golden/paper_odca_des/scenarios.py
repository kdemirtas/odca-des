"""paper-odca-des golden scenarios: S1-S4 and the lane-drop bottleneck in quick mode.

Copied from paper-odca-des `run_experiments.run_single` and `run_bottleneck.run_single_bottleneck`
(quick branch); the construction must stay identical to the paper's runners, so that
`fingerprint.json` proves the package reproduces that paper's runs (D-2026-09-19-8).
"""

from dataclasses import asdict
from config import HDV_VEHICLE, sim_config
from odca.params import NetworkConfig
from odca.analysis.metrics import summary_statistics
from odca.simulation.engine import Simulation

GOLDEN_SEEDS = [1, 2, 3]

MIXED_SCENARIOS = [
    ("S1_baseline", 0.0),
    ("S2_low_av", 0.3),
    ("S3_med_av", 0.5),
    ("S4_high_av", 0.7),
]

BOTTLENECK_SCENARIOS = [
    ("BN_0av", 0.0),
    ("BN_30av", 0.3),
    ("BN_50av", 0.5),
    ("BN_70av", 0.7),
]
BOTTLENECK_LANES = 3
BOTTLENECK_CELLS = 600
BOTTLENECK_CLOSED_LANE = 3
BOTTLENECK_CLOSURE_START = 300
BOTTLENECK_CLOSURE_END = 599
BOTTLENECK_MAINLINE_FLOW = 3600
BOTTLENECK_INITIAL_SPACING = 25


def _stats(results, config, av_penetration, seed):
    stats = summary_statistics(results.completed_vehicles, warmup=config.warmup,
                               sim_duration=config.sim_duration)
    stats["av_penetration"] = av_penetration
    stats["seed"] = seed
    stats["hdv_action_interval"] = config.hdv_driver.action_interval
    return stats, asdict(results.counters)


def run_mixed(av_penetration, seed):
    config = sim_config(av_penetration=av_penetration, seed=seed, sim_duration=300.0, warmup=30.0)
    return _stats(Simulation(config).run(), config, av_penetration, seed)


def run_bottleneck(av_penetration, seed):
    per_lane_flow = BOTTLENECK_MAINLINE_FLOW / BOTTLENECK_LANES
    config = sim_config(
        network=NetworkConfig.corridor(BOTTLENECK_LANES, BOTTLENECK_CELLS, HDV_VEHICLE.v_max),
        demand={f"mainline_lane_{lane}": {"end": per_lane_flow}
                for lane in range(1, BOTTLENECK_LANES + 1)},
        av_penetration=av_penetration, sim_duration=600.0, warmup=60.0, seed=seed,
    )
    sim = Simulation(config)
    sim.freeway.block_cells(lane_idx=BOTTLENECK_CLOSED_LANE, start_cell=BOTTLENECK_CLOSURE_START,
                            end_cell=BOTTLENECK_CLOSURE_END)
    sim.seed_vehicles(spacing=BOTTLENECK_INITIAL_SPACING, destination="end")
    return _stats(sim.run(), config, av_penetration, seed)


def golden_runs():
    """(run_id, callable returning (stats, counters)) for every fingerprinted run."""
    runs = []
    for label, av_penetration in MIXED_SCENARIOS:
        for seed in GOLDEN_SEEDS:
            runs.append((f"{label}_seed{seed}", lambda a=av_penetration, s=seed: run_mixed(a, s)))
    for label, av_penetration in BOTTLENECK_SCENARIOS:
        for seed in GOLDEN_SEEDS:
            run_id = f"{label}_seed{seed}"
            runs.append((run_id, lambda a=av_penetration, s=seed: run_bottleneck(a, s)))
    return runs
