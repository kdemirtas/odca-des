"""One run as a record: what was run, its summary statistics and counters, and extra data.

A record is written as one JSON file per (scenario, seed, action interval); the keys are the
per-seed JSON contract the aggregation and the paper figures read.
"""

from __future__ import annotations

import glob
import json
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, Iterator, Optional, Tuple

from odca.params import SimConfig
from odca.simulation.engine import Simulation
from odca.simulation.result import SimulationResult


def numpy_default(value: Any) -> Any:
    """`json.dump(..., default=numpy_default)`: numpy scalars become numbers, anything else fails.

    Args:
        value: the object json could not encode.

    Raises:
        TypeError: the object is not a numpy scalar.
    """
    if hasattr(value, "item") and callable(value.item):
        return value.item()
    raise TypeError(f"not JSON-serialisable in a result file: {type(value).__name__}")


@dataclass
class RunRecord:
    """One run: scenario label, AV share, seed, the two action intervals, and its results."""

    label: str
    av_penetration: float
    seed: int
    hdv_action_interval: float
    av_action_interval: float
    stats: Dict[str, Any]
    counters: Dict[str, int]
    extra: Dict[str, Any] = field(default_factory=dict)  # written as top-level keys

    @property
    def key(self) -> Tuple[str, float, float, int]:
        """What identifies the run: (label, AV share, HDV action interval, seed)."""
        return (self.label, self.av_penetration, self.hdv_action_interval, self.seed)

    def to_json(self) -> Dict[str, Any]:
        """The per-seed JSON object."""
        body = {k: v for k, v in asdict(self).items() if k != "extra"}
        return {**body, **self.extra}

    @classmethod
    def from_json(cls, payload: Dict[str, Any]) -> RunRecord:
        """A record from a per-seed JSON object.

        Args:
            payload: the parsed file.
        """
        known = {"label", "av_penetration", "seed", "hdv_action_interval",
                 "av_action_interval", "stats", "counters"}
        return cls(label=payload["label"], av_penetration=payload.get("av_penetration"),
                   seed=payload.get("seed"),
                   hdv_action_interval=payload.get("hdv_action_interval", 1.0),
                   av_action_interval=payload.get("av_action_interval"),
                   stats=payload.get("stats", {}), counters=payload.get("counters", {}),
                   extra={k: v for k, v in payload.items() if k not in known})


Measure = Callable[[SimulationResult], Dict[str, Any]]
Prepare = Callable[[Simulation], None]


def run_once(label: str, config: SimConfig, measure: Measure,
             prepare: Optional[Prepare] = None) -> Tuple[RunRecord, SimulationResult]:
    """Simulate `config` once and record it.

    Args:
        label: the scenario name.
        config: the run config (its seed and AV share are recorded).
        measure: summary statistics of the result; `wall_time_s` (the run alone) is added.
        prepare: changes the built simulation before it runs (blocked cells, vehicles
            placed at t=0).
    """
    sim = Simulation(config)
    if prepare is not None:
        prepare(sim)
    start = time.time()
    result = sim.run()
    wall_time = time.time() - start
    stats = measure(result)
    stats["wall_time_s"] = round(wall_time, 2)
    record = RunRecord(label, config.av_penetration, config.seed,
                       config.hdv_driver.action_interval, config.av_driver.action_interval,
                       stats, asdict(result.counters))
    return record, result


def write_run(path: Path, record: RunRecord):
    """Write `record` as its per-seed JSON file.

    Args:
        path: the file to write.
        record: the run.
    """
    with open(path, "w") as f:
        json.dump(record.to_json(), f, indent=2, default=numpy_default)


def read_runs(pattern: str) -> Iterator[RunRecord]:
    """Every per-seed JSON matching the glob `pattern`, in path order.

    Args:
        pattern: a recursive glob.

    Raises:
        ValueError: the same run (label, AV share, action interval, seed) appears twice.
        json.JSONDecodeError: a file is not valid JSON.
    """
    seen = {}
    for path in sorted(glob.glob(pattern, recursive=True)):
        with open(path) as f:
            record = RunRecord.from_json(json.load(f))
        if record.key in seen:
            raise ValueError(f"duplicate run {record.key}: {seen[record.key]} and {path}")
        seen[record.key] = path
        yield record
