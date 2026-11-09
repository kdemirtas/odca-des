"""Platoon measures over a run's trajectories (D-2026-11-05-5).

m-bar, the mean AV unit size, is counted at a section, per lane: the AV passages of the section's
cell in that lane after the warm-up (once per vehicle on an open road, once per lap on a ring,
D-2026-11-08-7), divided by the AV units among them, where a solo AV is a unit of 1 and a
platoon passing, whatever its size, is one unit. The AV share alpha is counted from the same crossings: AVs over
all vehicles. This section count is the m-bar the paper reports; the controller's on-road time
average is a diagnostic.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Tuple

from odca.entity.vehicle import Vehicle


@dataclass(frozen=True, slots=True)
class SectionCount:
    """Vehicles, AVs and AV units that crossed one section of one lane (or of every lane)."""

    cell_idx: int
    lane_idx: Optional[int]   # None: every lane
    vehicles: int
    avs: int
    units: int

    @property
    def unit_size(self) -> float:
        """m-bar: AVs per AV unit, 0 when no AV crossed."""
        return self.avs / self.units if self.units else 0.0

    @property
    def av_share(self) -> float:
        """alpha: AVs per vehicle crossing, 0 when none crossed."""
        return self.avs / self.vehicles if self.vehicles else 0.0


def count_av_units(vehicles: Iterable[Vehicle], cell_idx: int, start_time: float,
                   lane_idx: Optional[int] = None) -> SectionCount:
    """The vehicles, AVs and AV units passing cell `cell_idx` at or after `start_time`.

    Every passage counts, in the lane of its arrival: once per vehicle on an open road, once per
    lap on a ring (D-2026-11-08-7). A passage is an arrival in a cell with that index; a
    lane change into a cell with the same index is the same passage. A platoon passing is one
    unit: the passages of its members are grouped by platoon id, and a new unit starts when a
    member passes again. Needs the drivers' membership log, which `PlatoonDriver` keeps; an AV
    without it counts as solo.

    Args:
        vehicles: every vehicle of the run.
        cell_idx: the section.
        start_time: the warm-up end.
        lane_idx: count this lane only; None counts every lane.
    """
    crossing, avs, solo = 0, 0, 0
    platoon_passages: Dict[int, List[Tuple[float, int]]] = {}
    for vehicle in vehicles:
        for time, lane in _passages(vehicle, cell_idx):
            if time < start_time or (lane_idx is not None and lane != lane_idx):
                continue
            crossing += 1
            if vehicle.kind != "autonomous":
                continue
            avs += 1
            platoon_id = (vehicle.driver.platoon_id_at(time)
                          if hasattr(vehicle.driver, "platoon_id_at") else None)
            if platoon_id is None:
                solo += 1
            else:
                platoon_passages.setdefault(platoon_id, []).append((time, vehicle.id))
    platoon_units = sum(_train_passages(p) for p in platoon_passages.values())
    return SectionCount(cell_idx, lane_idx, crossing, avs, solo + platoon_units)


def _train_passages(passages: List[Tuple[float, int]]) -> int:
    """How many times one platoon passed: its members' (time, vehicle id) passages in time
    order, a new passage starting when a vehicle already in the current one passes again.

    Args:
        passages: the passages of one platoon's members.
    """
    count, current = 0, set()
    for _, vehicle_id in sorted(passages):
        if not current or vehicle_id in current:
            count += 1
            current = set()
        current.add(vehicle_id)
    return count


def section_counts(vehicles: List[Vehicle], cells: Iterable[int], lanes: Iterable[int],
                   start_time: float) -> List[SectionCount]:
    """One `SectionCount` per (section cell, lane).

    Args:
        vehicles: every vehicle of the run.
        cells: the section cells.
        lanes: the lane indices.
        start_time: the warm-up end.
    """
    lanes = list(lanes)
    return [count_av_units(vehicles, cell, start_time, lane) for cell in cells for lane in lanes]


def pooled(counts: Iterable[SectionCount]) -> Tuple[float, float]:
    """(m-bar, alpha) over several section counts: summed AVs over summed units, and summed
    AVs over summed vehicles.

    Args:
        counts: section counts.
    """
    counts = list(counts)
    vehicles = sum(c.vehicles for c in counts)
    avs = sum(c.avs for c in counts)
    units = sum(c.units for c in counts)
    return (avs / units if units else 0.0), (avs / vehicles if vehicles else 0.0)


def av_unit_size_at(vehicles: List[Vehicle], cells: Iterable[int], start_time: float) -> float:
    """m-bar pooled over several sections and every lane.

    Args:
        vehicles: every vehicle of the run.
        cells: the section cells.
        start_time: the warm-up end.
    """
    return pooled(count_av_units(vehicles, cell, start_time) for cell in cells)[0]


def _passages(vehicle: Vehicle, cell_idx: int) -> List[Tuple[float, int]]:
    """(time, lane) of each of `vehicle`'s passages of cell index `cell_idx`: every arrival in
    a cell with that index whose previous record was in another cell index.

    Args:
        vehicle: a vehicle.
        cell_idx: the cell index.
    """
    passages, previous = [], None
    for record in vehicle.trajectory:
        if record.cell_idx == cell_idx and previous != cell_idx:
            passages.append((record.time, record.lane_idx))
        previous = record.cell_idx
    return passages
