"""The NaSch baseline: the classical rules unchanged, and the posted limit (D-2026-09-20-19)."""

import pytest

from odca.baselines.nasch import NaSchConfig, NaSchSimulation

ZONE = range(80, 120)
LIMIT = 2
ROAD_CELLS = 200


def _road(limit_in_zone: bool):
    cells = tuple(
        LIMIT if (limit_in_zone and c in ZONE) else 5 for c in range(ROAD_CELLS)
    )
    return NaSchConfig(num_cells=ROAD_CELLS, v_max=5, slowdown_prob=0.0, density=0.15,
                       seed=11, cell_v_max=cells if limit_in_zone else None)


def _run(config, steps: int = 60):
    sim = NaSchSimulation(config)
    return [sim.step() for _ in range(steps)]


def test_unset_limit_leaves_the_classical_rules_alone():
    """`cell_v_max` unset is the model as it was: every cell allows `v_max`."""
    flat = NaSchConfig(num_cells=ROAD_CELLS, v_max=5, slowdown_prob=0.0, density=0.15,
                       seed=11, cell_v_max=tuple([5] * ROAD_CELLS))
    assert _run(_road(limit_in_zone=False)) == _run(flat)


def test_no_vehicle_crosses_a_cell_faster_than_it_allows():
    """A vehicle inside the zone holds at most the posted limit, outside it holds `v_max`."""
    for positions, speeds in _run(_road(limit_in_zone=True)):
        for pos, v in zip(positions, speeds):
            assert v <= (LIMIT if pos in ZONE else 5)


def test_the_limit_applies_to_the_cells_crossed_not_only_the_one_left():
    """A fast vehicle one cell before the zone enters it at the posted limit, not at `v_max`."""
    cells = tuple(LIMIT if c in ZONE else 5 for c in range(ROAD_CELLS))
    sim = NaSchSimulation(NaSchConfig(num_cells=ROAD_CELLS, v_max=5, slowdown_prob=0.0,
                                      density=0.0, seed=11, cell_v_max=cells))
    sim.road[:] = -1
    sim.road[78] = 5                      # at speed 5, two cells before the zone
    positions, speeds = sim.step()
    assert positions == [80] and speeds == [2]


def test_a_limit_of_the_wrong_length_is_refused():
    with pytest.raises(ValueError, match="cell_v_max"):
        NaSchSimulation(NaSchConfig(num_cells=ROAD_CELLS, cell_v_max=(5, 5, 5)))
