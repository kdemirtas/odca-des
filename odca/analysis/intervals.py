"""The one 95% confidence interval of the package (paper-odca-des D-2026-09-19-3, -9)."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Sequence

# two-sided 95% Student t quantiles by degrees of freedom; above 30 the normal 1.96 is used
_T95 = {
    1: 12.706, 2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571, 6: 2.447, 7: 2.365,
    8: 2.306, 9: 2.262, 10: 2.228, 11: 2.201, 12: 2.179, 13: 2.160, 14: 2.145,
    15: 2.131, 16: 2.120, 17: 2.110, 18: 2.101, 19: 2.093, 20: 2.086, 21: 2.080,
    22: 2.074, 23: 2.069, 24: 2.064, 25: 2.060, 26: 2.056, 27: 2.052, 28: 2.048,
    29: 2.045, 30: 2.042,
}


@dataclass(frozen=True, slots=True)
class Interval:
    """Mean, sample standard deviation and 95% interval of `n` values."""

    n: int
    mean: float
    std: float
    lo: float
    hi: float


def t95(df: int) -> float:
    """Two-sided 95% Student t quantile.

    Args:
        df: degrees of freedom, at least 1.
    """
    return _T95.get(df, 1.96)


def mean_ci95(values: Sequence[float]) -> Interval:
    """The mean and its 95% Student t interval; one value gives a zero-width interval.

    Args:
        values: one number per replication.
    """
    n = len(values)
    if n == 0:
        nan = float("nan")
        return Interval(0, nan, nan, nan, nan)
    mean = sum(values) / n
    if n == 1:
        return Interval(1, mean, 0.0, mean, mean)
    std = math.sqrt(sum((v - mean) ** 2 for v in values) / (n - 1))
    sem = std / math.sqrt(n)
    t = t95(n - 1)
    return Interval(n, mean, std, mean - t * sem, mean + t * sem)
