"""What a lane-change model sees in one lane: the gaps and speeds around the vehicle."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class NeighbourState:
    """The leader and follower in one lane, seen from a cell beside or under the vehicle."""

    gap_front: float     # cells to the leader; the look-ahead range when there is none
    v_leader: float      # cells/s; the vehicle's top speed when there is none
    has_leader: bool
    gap_rear: float      # cells to the follower; the look-behind range when there is none
    v_follower: float    # cells/s; 0 when there is none
    has_follower: bool

    @property
    def lane_speed(self) -> float:
        """The speed the lane offers: its leader's, or the top speed on an open lane."""
        return self.v_leader


def _cells_to(cell, other, step: str) -> float:
    """Cells from `cell` to `other`, walking `step` (`next` or `previous`); works on a ring.

    Args:
        cell: where the walk starts.
        other: the cell to reach; it lies within the scan range.
        step: the neighbour link to follow.
    """
    count = 0
    while cell is not other:
        cell = getattr(cell, step)
        count += 1
    return float(count)


def observe(cell, driver) -> NeighbourState:
    """The neighbour state of the lane `cell` is in, as `driver` sees it.

    Args:
        cell: the vehicle's own cell, or the cell beside it in the lane of interest.
        driver: the deciding driver; gives the look-ahead and look-behind ranges.
    """
    leader = cell.find_leader(driver.look_ahead)
    follower = cell.find_follower(driver.look_behind)
    return NeighbourState(
        gap_front=_cells_to(cell, leader.cell, "next") if leader else float(driver.look_ahead),
        v_leader=leader.speed if leader else driver.vehicle.cfg.v_max,
        has_leader=leader is not None,
        gap_rear=(_cells_to(cell, follower.cell, "previous") if follower
                  else float(driver.look_behind)),
        v_follower=follower.speed if follower else 0.0,
        has_follower=follower is not None,
    )
