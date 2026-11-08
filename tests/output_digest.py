"""Full-output digests of representative runs, to show a change leaves them byte-identical.

The goldens compare summary statistics; this compares everything a run produces: every
vehicle's trajectory (each T(x, n) record), lane changes, entry and exit times and counters,
the run counters and the platoon statistics, plus the validated config. Run it on the base
code and on the change and compare the files (D-2026-11-08-1):

    uv run python tests/output_digest.py after.json [--shard 0/4]
    uv run python tests/output_digest.py before.json --base build/base [--shard 0/4]

`--base DIR` imports `odca` from DIR (a copy of the package as it is on the base commit)
instead of the working tree. `--shard i/n` runs every n-th run from the i-th, so n processes
cover all runs in parallel; merge the shard files before comparing.

Runs: every golden run of every paper, the 13 paper-odca-platoon scenarios (quick, seed 42),
and a one-lane ring made with `Lane.make_periodic` and seeded platoons, as the platoon paper's
fundamental-diagram script builds it.
"""

import argparse
import hashlib
import json
import sys
from dataclasses import asdict
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
GOLDEN_DIR = TESTS_DIR / "golden"
# config lines of fields the change adds, at their off value: the config echo of a run gains
# them, nothing else does, so they are left out to compare with a base that lacks the field.
# Empty this set once the base has the field.
NEW_FIELDS_AT_DEFAULT = {"ring: false", "missed_exit_laps: 1"}


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
        "config": "".join(line for line in result.config_yaml().splitlines(keepends=True)
                          if line.strip() not in NEW_FIELDS_AT_DEFAULT),
    }
    text = json.dumps(payload, sort_keys=True)
    return {"sha256": hashlib.sha256(text.encode()).hexdigest(),
            "vehicles": len(vehicles),
            "records": sum(len(v["trajectory"]) for v in vehicles)}


def _jobs(engine, load_paper):
    """(key, callable returning the run's `SimulationResult`s) for every run, in fixed order.

    Args:
        engine: the `odca.simulation.engine` module in use.
        load_paper: imports one golden paper's `scenarios` module.
    """
    captured = []
    original_run = engine.Simulation.run

    def capturing_run(self):
        result = original_run(self)
        captured.append(result)
        return result

    engine.Simulation.run = capturing_run

    def golden(run):
        def go():
            captured.clear()
            run()
            return list(captured)
        return go

    def scenario(scenarios, av_penetration, strategy):
        def go():
            config = scenarios.scenario_config(av_penetration, strategy, 42, quick=True)
            return [engine.Simulation(config).run()]
        return go

    def make_periodic_ring(scenarios):
        def go():
            config = scenarios.scenario_config(0.7, "dcp", 42, quick=True)
            sim = engine.Simulation(config)
            sim.freeway.lane(1).make_periodic()
            sim.freeway.destination = lambda name: None
            sim.seed_platoons(platoon_size=4, gap=6, destination="end")
            return [sim.run()]
        return go

    jobs = []
    for paper_dir in sorted(p for p in GOLDEN_DIR.iterdir() if p.is_dir()):
        scenarios = load_paper(paper_dir)
        for run_id, run in scenarios.golden_runs():
            jobs.append((f"{paper_dir.name}:{run_id}", golden(run), scenarios))
        if paper_dir.name == "paper_odca_platoon":
            for label, av_penetration, strategy in scenarios.SCENARIOS:
                jobs.append((f"paper_odca_platoon:scenario:{label}",
                             scenario(scenarios, av_penetration, strategy), scenarios))
            jobs.append(("paper_odca_platoon:make_periodic_ring",
                         make_periodic_ring(scenarios), scenarios))
    return jobs


def main():
    """Write the digest of every run (of this shard) to the output file."""
    parser = argparse.ArgumentParser()
    parser.add_argument("out_path")
    parser.add_argument("--base", help="directory holding the base commit's odca package")
    parser.add_argument("--shard", default="0/1", help="i/n: every n-th run from the i-th")
    args = parser.parse_args()
    if args.base:
        sys.path.insert(0, str(Path(args.base).resolve()))
    sys.path.insert(0, str(TESTS_DIR))
    import odca
    from odca.simulation import engine
    from test_golden import _load_paper
    print("odca from", Path(odca.__file__).parent, flush=True)

    index, count = (int(x) for x in args.shard.split("/"))
    digests = {}
    for position, (key, go, _) in enumerate(_jobs(engine, _load_paper)):
        if position % count != index:
            continue
        for i, result in enumerate(go()):
            digests[f"{key}:{i}"] = digest(result)
        print(key, flush=True)
    Path(args.out_path).write_text(json.dumps(digests, indent=1, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
