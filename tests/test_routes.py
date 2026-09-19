"""Named origins and destinations, built by the freeway (D-2026-09-19-26)."""

import pytest
import simpy

from odca.infrastructure.freeway import Freeway
from odca.params import DestinationConfig, NetworkConfig, OriginConfig


def _network(**changes):
    network = dict(
        num_lanes=4, num_cells=800, speed_limit=5.2,
        origins={"mainline_lane_3": OriginConfig(3), "onramp_1": OriginConfig(1, 100)},
        destinations={"offramp_1": DestinationConfig(300, 1),
                      "end_lane_4": DestinationConfig(800, 4), "end": DestinationConfig(800)},
    )
    network.update(changes)
    return NetworkConfig(**network)


@pytest.fixture
def freeway():
    return Freeway(simpy.Environment(), _network())


def test_origins_are_cells(freeway):
    assert (freeway.origin("mainline_lane_3").cell.lane.idx, freeway.origin("onramp_1").cell.idx) \
        == (3, 100)


def test_destinations_mark_their_exit_cells(freeway):
    def leaves_to(lane, cell):
        return [exit_cell.destination.name for exit_cell in freeway.cell(lane, cell).exits]

    assert freeway.destination("offramp_1").is_offramp
    assert leaves_to(1, 299) == ["offramp_1"] and leaves_to(2, 299) == []
    assert not freeway.destination("end").is_offramp
    assert all("end" in leaves_to(lane, 799) for lane in (1, 2, 3, 4))
    assert leaves_to(4, 799) == ["end_lane_4", "end"]
    assert freeway.origin("onramp_1").entry.road_cell is freeway.cell(1, 100)


def test_ramp_cells_come_from_the_named_places():
    network = _network()
    assert (network.onramp_cells, network.offramp_cells) == ([100], [300])


@pytest.mark.parametrize("name", ["offramp_2", "end_lane_1", "800"])
def test_unknown_destination_is_refused(freeway, name):
    with pytest.raises(ValueError, match="unknown destination"):
        freeway.destination(name)


def test_unknown_origin_is_refused(freeway):
    with pytest.raises(ValueError, match="unknown origin"):
        freeway.origin("onramp_2")


@pytest.mark.parametrize("changes", [
    {"origins": {"x": OriginConfig(5)}},
    {"destinations": {"x": DestinationConfig(801)}},
    {"destinations": {"x": DestinationConfig(300, 0)}},
])
def test_places_off_the_road_are_refused(changes):
    with pytest.raises(ValueError, match="off the road"):
        Freeway(simpy.Environment(), _network(**changes))


def test_corridor_has_every_lane_end():
    network = NetworkConfig.corridor(3, 600, 5.2)
    assert sorted(network.origins) == ["mainline_lane_1", "mainline_lane_2", "mainline_lane_3"]
    assert sorted(network.destinations) == ["end", "end_lane_1", "end_lane_2", "end_lane_3"]
