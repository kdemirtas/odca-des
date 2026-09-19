"""The experiment kit and the one 95% interval (D-2026-09-19-33)."""

import csv
import json
import math

import numpy as np
import pytest

from odca.analysis.intervals import mean_ci95
from odca.simulation.engine import Simulation
from odca.experiment import (RunRecord, aggregate, numpy_default, read_runs, run_once,
                             write_aggregate_csv, write_run)


def _record(seed, label="S1_baseline", **stats):
    return RunRecord(label, 0.0, seed, 1.0, 0.1, stats, {"lane_changes": 1},
                     {"fd_data": {"300": []}})


def test_interval_matches_student_t():
    ci = mean_ci95([1.0, 2.0, 3.0, 4.0])
    half = 3.182 * math.sqrt(sum((v - 2.5) ** 2 for v in [1, 2, 3, 4]) / 3) / 2
    assert (ci.n, ci.mean) == (4, 2.5)
    assert ci.lo == pytest.approx(2.5 - half) and ci.hi == pytest.approx(2.5 + half)
    assert mean_ci95([7.0]).lo == 7.0 and mean_ci95([]).n == 0


def test_a_record_round_trips_through_its_file(tmp_path):
    write_run(tmp_path / "S1_seed1.json", _record(1, avg_delay=np.float64(12.5)))
    (back,) = read_runs(str(tmp_path / "*.json"))
    assert back == _record(1, avg_delay=12.5)
    assert json.loads((tmp_path / "S1_seed1.json").read_text())["fd_data"] == {"300": []}


def test_a_seed_seen_twice_is_refused(tmp_path):
    for batch in ("batch1", "batch2"):
        (tmp_path / batch).mkdir()
        write_run(tmp_path / batch / "S1_seed1.json", _record(1))
    with pytest.raises(ValueError, match="duplicate run"):
        list(read_runs(str(tmp_path / "batch*" / "*.json")))


def test_an_unreadable_file_is_refused(tmp_path):
    (tmp_path / "broken.json").write_text("{not json")
    with pytest.raises(json.JSONDecodeError):
        list(read_runs(str(tmp_path / "*.json")))


def test_unknown_objects_fail_instead_of_becoming_strings():
    assert json.loads(json.dumps({"n": np.int64(3)}, default=numpy_default)) == {"n": 3}
    with pytest.raises(TypeError):
        json.dumps({"vehicle": object()}, default=numpy_default)


def test_aggregate_groups_and_writes_the_csv_schema(tmp_path):
    records = [_record(s, avg_delay=float(s)) for s in (1, 2, 3)]
    records.append(_record(1, "S2", avg_delay=5.0))
    rows = aggregate(records, ["avg_delay", "throughput_per_hour"])
    assert [(r.group[0], r.metric, r.interval.n) for r in rows] == [
        ("S1_baseline", "avg_delay", 3), ("S2", "avg_delay", 1)]
    write_aggregate_csv(tmp_path / "aggregate.csv", rows)
    with open(tmp_path / "aggregate.csv") as f:
        first = next(csv.DictReader(f))
    assert list(first) == ["scenario", "av_penetration", "hdv_action_interval", "metric", "n",
                           "mean", "std", "ci95_lo", "ci95_hi"]
    assert first["mean"] == "2.000000"


def test_run_once_prepares_runs_and_records(tmp_path):
    import sys
    from dataclasses import asdict
    sys.path.insert(0, "tests/golden/paper_odca_des")
    try:
        from config import sim_config
    finally:
        sys.path.remove("tests/golden/paper_odca_des")
        sys.modules.pop("config", None)
    from odca.params import NetworkConfig
    config = sim_config(network=NetworkConfig.corridor(2, 60, 5.2),
                        demand={"mainline_lane_1": {"end": 600.0}},
                        sim_duration=60.0, warmup=0.0, seed=5)
    seen = []
    record, result = run_once("demo", config, lambda r: {"completed": r.num_completed},
                              prepare=lambda sim: (seen.append(sim),
                                                   sim.seed_vehicles(20, "end")))
    assert len(seen) == 1 and result.num_generated < len(result.vehicles)  # placed at t=0
    assert record.key == ("demo", 0.0, config.hdv_driver.action_interval, 5)
    assert record.counters == asdict(result.counters)
    assert record.stats["completed"] == result.num_completed and "wall_time_s" in record.stats
    assert Simulation(config).run().counters != result.counters  # the prepare hook mattered


def test_extra_keys_cannot_overwrite_the_record():
    record = _record(1)
    record.extra["seed"] = 99
    with pytest.raises(ValueError, match="seed"):
        record.to_json()
