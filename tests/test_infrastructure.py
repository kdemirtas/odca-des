"""Cell links and the lane's count of closed cells (D-2026-09-19-35)."""

import simpy

from odca.infrastructure.freeway import Freeway
from odca.params import NetworkConfig


def two_lanes(num_cells=20):
    return Freeway(simpy.Environment(), NetworkConfig.corridor(2, num_cells, 5.2))


def test_side_and_diagonal_links_follow_the_lanes():
    freeway = two_lanes()
    right, left = freeway.lane(1), freeway.lane(2)
    cell = right.cells[5]
    assert cell.left is left.cells[5] and cell.right is None
    assert cell.left_next is left.cells[6] and cell.left_prev is left.cells[4]
    assert left.cells[5].right_next is right.cells[6]
    assert right.cells[-1].left_next is None and right.cells[0].left_prev is None


def test_blockage_scan_sees_only_closed_cells_of_its_lane():
    freeway = two_lanes()
    right, left = freeway.lane(1), freeway.lane(2)
    left.cells[8].blocked = True
    assert (left.blocked_count, right.blocked_count) == (1, 0)
    assert right.cells[5].find_blockage(10) is None
    assert left.cells[5].find_blockage(10) == 3
    left.cells[8].blocked = True  # closing a closed cell does not count twice
    left.cells[8].blocked = False
    assert left.blocked_count == 0 and left.cells[5].find_blockage(10) is None


def test_periodic_lane_wraps_and_relinks_the_diagonals():
    freeway = two_lanes()
    right, left = freeway.lane(1), freeway.lane(2)
    right.make_periodic()
    assert right.cells[-1].next is right.cells[0]
    assert right.cells[0].previous is right.cells[-1]
    assert left.cells[-1].right_next is right.cells[0]
    right.cells[2].blocked = True
    assert right.cells[-1].find_blockage(5) == 3
