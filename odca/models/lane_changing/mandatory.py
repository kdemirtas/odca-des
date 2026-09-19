"""Mandatory lane change (MLC) probability using a logistic function.

P_MLC(r, n) = scale / (1 + exp(-k * (r0 * n - r)))

where:
    r = remaining distance ratio (1.0 at origin, 0.0 at destination)
    n = number of lane changes still needed
    k = steepness parameter
    r0 = midpoint for single lane change
    scale ensures P → 1.0 as r → 0
"""

import math

# The MLC curve is a probability per this many cells driven: one second of free flow at
# v_max = 5.2 cells/s, so free-flow HDV behaviour matches the per-decision calibration
# (D-2026-09-19-22).
MLC_REFERENCE_CELLS = 5.2


def mlc_probability(
    remaining_ratio: float,
    num_lane_changes: int,
    k: float,
    r0: float,
    force_threshold: float = 0.05,
) -> float:
    """Compute MLC probability.

    Args:
        remaining_ratio: Fraction of trip remaining (0 to 1).
        num_lane_changes: Lane changes still needed to reach exit lane.
        k: Logistic steepness.
        r0: Midpoint for single lane change.
        force_threshold: Below this ratio, probability is forced to 1.0.

    Returns:
        Probability of initiating a lane change (0 to 1).
    """
    if num_lane_changes <= 0:
        return 0.0
    if remaining_ratio <= force_threshold:
        return 1.0

    effective_r0 = r0 * num_lane_changes
    x = k * (effective_r0 - remaining_ratio)
    base_prob = 1.0 / (1.0 + math.exp(-x))
    # Scale so that P → 1 as r → 0
    scale = 1.0 + math.exp(-k * effective_r0)
    return min(1.0, base_prob * scale)
