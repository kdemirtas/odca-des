"""Tables from run records: one row per run, and one row per (group, metric) with its 95%
interval. The aggregate CSV grain is (scenario, AV share, action interval, metric)."""

from __future__ import annotations

import csv
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Sequence, Tuple

from odca.analysis.intervals import Interval, mean_ci95
from odca.experiment.records import RunRecord


@dataclass(frozen=True, slots=True)
class AggregateRow:
    """One metric of one group of runs (same label, AV share and HDV action interval)."""

    group: Tuple[str, float, float]
    metric: str
    interval: Interval


def aggregate(records: Iterable[RunRecord], metrics: Sequence[str]) -> List[AggregateRow]:
    """Mean and 95% interval of each metric over the seeds of each group, groups sorted.

    Args:
        records: the runs.
        metrics: stats keys to aggregate, in output order; a missing value is left out.
    """
    groups: Dict[Tuple, Dict[str, List[float]]] = defaultdict(lambda: defaultdict(list))
    for record in records:
        group = (record.label, record.av_penetration, record.hdv_action_interval)
        for metric in metrics:
            value = record.stats.get(metric)
            if value is not None:
                groups[group][metric].append(value)
    return [AggregateRow(group, metric, mean_ci95(values))
            for group, by_metric in sorted(groups.items())
            for metric, values in by_metric.items()]


def write_aggregate_csv(path: Path, rows: Iterable[AggregateRow],
                        interval_column: str = "hdv_action_interval"):
    """Write the aggregate CSV: scenario, AV share, action interval, metric, n, mean, std, CI.

    Args:
        path: the file to write.
        rows: from `aggregate`.
        interval_column: the header of the action-interval column.
    """
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["scenario", "av_penetration", interval_column, "metric",
                    "n", "mean", "std", "ci95_lo", "ci95_hi"])
        for row in rows:
            label, av_penetration, action_interval = row.group
            i = row.interval
            w.writerow([label, av_penetration, action_interval, row.metric, i.n,
                        f"{i.mean:.6f}", f"{i.std:.6f}", f"{i.lo:.6f}", f"{i.hi:.6f}"])


def write_per_seed_csv(path: Path, records: Iterable[RunRecord], metrics: Sequence[str],
                       order: Callable[[RunRecord], tuple]):
    """Write one row per run: label, AV share, seed, action interval, then the metrics.

    Args:
        path: the file to write.
        records: the runs.
        metrics: stats keys, one column each.
        order: sort key of the rows.
    """
    fieldnames = ["label", "av_penetration", "seed", "hdv_action_interval", *metrics]
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in sorted(records, key=order):
            w.writerow({"label": r.label, "av_penetration": r.av_penetration, "seed": r.seed,
                        "hdv_action_interval": r.hdv_action_interval,
                        **{m: r.stats.get(m) for m in metrics}})
