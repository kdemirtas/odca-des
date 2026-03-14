"""Newell's simplified car-following model.

Desired spacing: s*(v) = d + v * tau
where d = standstill spacing, tau = reaction time, v = leader speed.

Speed adjustment: if current spacing < desired, slow down; if >, speed up.
"""


def desired_spacing(leader_speed: float, tau: float, d: float) -> float:
    """Compute desired spacing given leader speed.

    Args:
        leader_speed: Speed of the leading vehicle (cells/s).
        tau: Reaction time (s).
        d: Standstill spacing (cells).

    Returns:
        Desired spacing in cells.
    """
    return d + leader_speed * tau


def desired_speed(
    current_spacing: float,
    leader_speed: float,
    tau: float,
    d: float,
    v_max: float,
) -> float:
    """Compute desired speed to converge to desired spacing.

    Uses Newell's logic: adjust speed based on spacing error.

    Args:
        current_spacing: Current gap to leader (cells).
        leader_speed: Leader's speed (cells/s).
        tau: Reaction time (s).
        d: Standstill spacing (cells).
        v_max: Maximum allowed speed (cells/s).

    Returns:
        Desired speed (cells/s), clamped to [0, v_max].
    """
    s_star = desired_spacing(leader_speed, tau, d)
    delta_s = current_spacing - s_star
    v_des = leader_speed + delta_s
    return max(0.0, min(v_des, v_max))
