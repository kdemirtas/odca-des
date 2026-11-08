"""Full-output digests of representative runs, to show a change leaves them byte-identical.

The goldens compare summary statistics; this compares everything a run produces: every
vehicle's trajectory (each T(x, n) record), lane changes, entry and exit times and counters,
the run counters and the platoon statistics, plus the validated config. Run it on the base
commit and on the change and compare the two files (D-2026-11-08-1):

    uv run python tests/output_digest.py before.json
    uv run python tests/output_digest.py after.json

Runs: every golden run of every paper, the 13 paper-odca-platoon scenarios (quick, seed 42),
and a one-lane ring made with `Lane.make_periodic` and seeded platoons, as the platoon paper's
fundamental-diagram script builds it.
"""

import hashlib
import json
import sys
from dataclasses import asdict
from pathlib import Path

GOLDEN_DIR = Path(__file__).resolve().parent / "golden"
sys.path.insert(0, str(Path(__file__).resolve().parent))

from test_golden import _load_paper  # noqa: E402

from odca.simulation import engine  # noqa: E402


def digest(result) -> dict:
    """SHA-256 of everything `result` holds, and its vehicle and record counts.

    Args:
        result: a `SimulationResult`.
    """
    vehicles = []
    for vehicle in result.vehicles:
        vehicles.append({
            "id": vehicle.id, "kind": vehicle.kind,
            "created": repr(vehicle.time_created), "entered": repr(vehicle.time_entered),
            "exited": repr(vehicle.time_exited),
            "destination": [vehicle.destination_cell_idx, vehicle.destination_lane],
            "trajectory": [repr(asdict(r)) for r in vehicle.trajectory],
            "lane_changes": [repr(asdict(r)) for r in vehicle.lane_changes],
            "counts": [vehicle.count_lane_changes, vehicle.count_lc_patience_failures,
                       vehicle.count_missed_exits],
        })
    payload = {
        "vehicles": vehicles,
        "generated": result.num_generated,
        "counters": repr(asdict(result.counters)),
        "platoons": repr(asdict(result.platoons)) if result.platoons is not None else None,
        "config": result.config_yaml(),
    }
    text = json.dumps(payload, sort_keys=True)
    return {"sha256": hashlib.sha256(text.encode()).hexdigest(),
            "vehicles": len(vehicles),
            "records": sum(len(v["trajectory"]) for v in vehicles)}


def main(out_path: str):
    """Write the digest of every run to `out_path`.

    Args:
        out_path: the JSON file to write.
    """
    captured = []
    original_run = engine.Simulation.run

    def capturing_run(self):
        result = original_run(self)
        captured.append(result)
        return result

    engine.Simulation.run = capturing_run
    digests = {}
    for paper_dir in sorted(p for p in GOLDEN_DIR.iterdir() if p.is_dir()):
        scenarios = _load_paper(paper_dir)
        for run_id, run in scenarios.golden_runs():
            captured.clear()
            run()
            for i, result in enumerate(captured):
                digests[f"{paper_dir.name}:{run_id}:{i}"] = digest(result)
            print(run_id, flush=True)
        if paper_dir.name == "paper_odca_platoon":
            for label, av_penetration, strategy in scenarios.SCENARIOS:
                config = scenarios.scenario_config(av_penetration, strategy, 42, quick=True)
                result = engine.Simulation(config).run()
                digests[f"paper_odca_platoon:scenario:{label}"] = digest(result)
                print(label, flush=True)
            # the fundamental-diagram ring: one lane joined end to end, platoons that never exit
            config = scenarios.scenario_config(0.7, "dcp", 42, quick=True)
            sim = engine.Simulation(config)
            sim.freeway.lane(1).make_periodic()
            sim.freeway.destination = lambda name: None
            sim.seed_platoons(platoon_size=4, gap=6, destination="end")
            digests["paper_odca_platoon:make_periodic_ring"] = digest(sim.run())
            print("make_periodic_ring", flush=True)
    Path(out_path).write_text(json.dumps(digests, indent=1, sort_keys=True) + "\n")


if __name__ == "__main__":
    main(sys.argv[1])
