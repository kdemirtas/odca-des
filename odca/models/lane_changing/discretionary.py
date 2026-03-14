"""Discretionary lane change (DLC) probability using a logistic function.

P_DLC(dv) = 1 / (1 + exp(-k * (dv - v0)))

where:
    dv = target_lane_speed - current_speed (speed advantage)
    k = steepness parameter
    v0 = minimum speed differential threshold
"""

import math


def dlc_probability(
    target_lane_speed: float,
    current_speed: float,
    k: float,
    v0: float,
) -> float:
    """Compute DLC probability based on speed advantage.

    Args:
        target_lane_speed: Speed in the target lane (cells/s).
        current_speed: Vehicle's current speed (cells/s).
        k: Logistic steepness.
        v0: Speed differential threshold (cells/s).

    Returns:
        Probability of discretionary lane change (0 to 1).
    """
    delta_v = target_lane_speed - current_speed
    x = k * (delta_v - v0)
    return 1.0 / (1.0 + math.exp(-x))
