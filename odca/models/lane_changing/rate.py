"""Convert a lane-change probability per unit of exposure into one for any exposure.

The MLC and DLC curves give a probability per unit: per 5.2 cells driven (MLC) or per second
(DLC). An evaluation covering `exposure` units uses q = 1 - (1 - p)^exposure, the same
constant-hazard conversion at any evaluation rate (D-2026-09-19-22, docs/lane-change-rate.md).
"""


def probability_over(p_per_unit: float, exposure: float) -> float:
    """Probability of a lane change over `exposure` units, given the probability per unit.

    Args:
        p_per_unit: probability per unit of exposure, in [0, 1]; 1 means certain (forced).
        exposure: units since the previous evaluation (cells / reference, or seconds), >= 0.

    Returns:
        q in [0, 1]: 1 for a forced change, 0 when no exposure has passed.
    """
    if p_per_unit >= 1.0:
        return 1.0
    if exposure <= 0.0 or p_per_unit <= 0.0:
        return 0.0
    return 1.0 - (1.0 - p_per_unit) ** exposure


def exposures(rule: str, elapsed: float, reference_distances: float):
    """The exposure of the mandatory and the discretionary curve over one evaluation.

    What one unit of exposure is depends on the rate rule (D-2026-10-03-4): `distance`, MLC
    per reference distance driven and DLC per second (the model's rule); `second`, both per
    second; `evaluation`, both per evaluation, so the curve's value is used as it is however
    often the driver evaluates.

    Args:
        rule: `distance`, `second` or `evaluation`.
        elapsed: seconds since the previous evaluation.
        reference_distances: distance driven since then, in reference distances.

    Returns:
        (mlc_exposure, dlc_exposure).

    Raises:
        ValueError: `rule` is none of the three.
    """
    if rule == "distance":
        return reference_distances, elapsed
    if rule == "second":
        return elapsed, elapsed
    if rule == "evaluation":
        return 1.0, 1.0
    raise ValueError(f"unknown rate rule {rule!r}")
