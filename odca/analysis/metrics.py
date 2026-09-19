"""Metrics computation from T(x, n) trajectory data."""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from odca.params import CELL_LENGTH_M
from odca.entity.vehicle import Vehicle, TrajectoryRecord


# ──────────────────────────────────────────────────────────────────────
# Edie's generalized definitions (space-time region)
# ──────────────────────────────────────────────────────────────────────

def edie_fd_points(
    vehicles: List[Vehicle],
    region_lo: int,
    region_hi: int,
    warmup: float,
    duration: float,
    interval: float = 20.0,
    num_lanes: int = 1,
) -> List[dict]:
    """Compute FD points using Edie's generalized definitions over T(x,n).

    For each time window [t, t+interval):
      D = total distance traveled in the region (cells)
      W = total time spent in the region (seconds)
      A = region_length × interval (cell·seconds)

      q = D / A   (flow, veh/s per cell-width)
      k = W / A   (density, veh per cell)
      v = D / W   (space-mean speed, cells/s)

    Distance and time are clipped to the measurement window boundaries.
    """
    region_len = region_hi - region_lo

    # Build cell-occupancy segments: (cell_idx, t_enter, t_leave)
    # Each segment represents one vehicle occupying one cell.
    segments = []
    for v in vehicles:
        traj = v.trajectory
        for j in range(len(traj) - 1):
            cell_idx = traj[j].cell_idx
            if region_lo <= cell_idx < region_hi:
                segments.append((traj[j].time, traj[j + 1].time))
        # Last record: vehicle still in cell at simulation end (or exited)
        if traj:
            last = traj[-1]
            if region_lo <= last.cell_idx < region_hi:
                t_leave = v.time_exited if v.time_exited is not None else duration
                if t_leave > last.time:
                    segments.append((last.time, t_leave))

    # Aggregate per window
    fd_points = []
    t = warmup
    while t + interval <= duration:
        t_end = t + interval
        total_time = 0.0
        total_dist = 0.0

        for t_enter, t_leave in segments:
            # Clip to window
            t0 = max(t_enter, t)
            t1 = min(t_leave, t_end)
            if t0 >= t1:
                continue
            seg_duration = t_leave - t_enter
            total_time += (t1 - t0)
            # Distance: fraction of 1 cell traversed in the clipped window
            total_dist += (t1 - t0) / seg_duration if seg_duration > 0 else 0.0

        area = region_len * interval * num_lanes
        if total_time > 0:
            k = total_time / area
            q = total_dist / area
            v_s = total_dist / total_time
            fd_points.append({
                "time": t,
                "flow": q,
                "density": k,
                "speed": v_s,
                "flow_vph": q * 3600,
                "density_vpkm": k * 1000 / CELL_LENGTH_M,
                "speed_kmh": v_s * CELL_LENGTH_M * 3.6,
            })
        t += interval

    return fd_points


def travel_time(vehicle: Vehicle) -> Optional[float]:
    """Total travel time for a completed vehicle."""
    if vehicle.time_entered is not None and vehicle.time_exited is not None:
        return vehicle.time_exited - vehicle.time_entered
    return None


def delay(vehicle: Vehicle) -> Optional[float]:
    """Per-cell delay: sum over cells of max(0, T_arr(c+1) - T_arr(c) - l / v_f).

    T_arr are the arrival times in the trajectory, l is one cell and v_f the vehicle's
    maximum speed; only cells crossed slower than free flow add delay (D-2026-09-19-15).
    """
    if vehicle.time_exited is None or vehicle.cfg.v_max <= 0:
        return None
    free_flow_cell_time = 1.0 / vehicle.cfg.v_max
    traj = vehicle.trajectory
    return sum(max(0.0, traj[j + 1].time - traj[j].time - free_flow_cell_time)
               for j in range(len(traj) - 1))


def cell_speeds(vehicle: Vehicle) -> List[float]:
    """Compute travel speed at each cell from trajectory records.

    Speed at cell c = cell_length / (T(c+1) - T(c)), including wait time.
    """
    traj = vehicle.trajectory
    speeds = []
    for i in range(len(traj) - 1):
        dt = traj[i + 1].time - traj[i].time
        if dt > 0:
            speeds.append(1.0 / dt)  # cells/s (1 cell per transition)
        else:
            speeds.append(float("inf"))
    return speeds


def count_lane_changes(vehicle: Vehicle) -> int:
    """Count number of lane changes from trajectory."""
    traj = vehicle.trajectory
    changes = 0
    for i in range(1, len(traj)):
        if traj[i].lane_idx != traj[i - 1].lane_idx:
            changes += 1
    return changes


def passage_time_flow(
    vehicles: List[Vehicle],
    measurement_cell: int,
    time_interval: float = 60.0,
    sim_duration: float = 3600.0,
) -> List[Tuple[float, float, float]]:
    """Compute flow, density, speed at a measurement cell over time intervals.

    Uses passage-time data to compute:
      q = N_pass / dt
      v_bar = harmonic mean of the passing vehicles' cell speeds (space-mean speed)
      k = q / v_bar

    Returns:
        List of (time_start, flow_veh_per_s, density, speed) tuples.
    """
    # Collect all passage times at measurement_cell
    passages = []  # (time, speed_at_cell)
    for veh in vehicles:
        for i, rec in enumerate(veh.trajectory):
            if rec.cell_idx == measurement_cell:
                # Speed = 1 / (T(c+1) - T(c)) if we have the next record
                if i + 1 < len(veh.trajectory):
                    dt = veh.trajectory[i + 1].time - rec.time
                    spd = 1.0 / dt if dt > 0 else veh.speed
                else:
                    spd = rec.speed
                passages.append((rec.time, spd))
                break  # first passage only (single direction)

    passages.sort(key=lambda x: x[0])

    results = []
    t = 0.0
    while t < sim_duration:
        t_end = t + time_interval
        interval_passages = [
            (pt, s) for pt, s in passages if t <= pt < t_end
        ]
        n = len(interval_passages)
        q = n / time_interval
        if n > 0:
            # space-mean speed (harmonic mean of spot speeds), so k = q / v holds
            inverse_speeds = [1.0 / s for _, s in interval_passages if s > 0]
            v_bar = len(inverse_speeds) / sum(inverse_speeds) if inverse_speeds else 0.0
            k = q / v_bar if v_bar > 0 else 0.0
        else:
            v_bar = 0.0
            k = 0.0
        results.append((t, q, k, v_bar))
        t = t_end

    return results


def summary_statistics(
    vehicles: List[Vehicle],
    warmup: float = 300.0,
    sim_duration: float = 3600.0,
) -> Dict:
    """Aggregate metrics over the vehicles that exit during the measurement period.

    The measurement period is [warmup, sim_duration]; a vehicle counts when it exits in it,
    whenever it entered (D-2026-09-19-14).
    """
    completed = [
        v for v in vehicles
        if v.time_exited is not None and v.time_entered is not None
        and warmup <= v.time_exited <= sim_duration
    ]

    if not completed:
        return {"num_completed": 0}

    tts = [travel_time(v) for v in completed]
    delays = [delay(v) for v in completed]
    lc_counts = [count_lane_changes(v) for v in completed]

    tts = [t for t in tts if t is not None]
    delays = [d for d in delays if d is not None]

    def mean(xs):
        return sum(xs) / len(xs) if xs else 0.0

    lc_per_km = []
    for v, lc in zip(completed, lc_counts):
        cells_driven = v.trajectory[-1].cell_idx - v.trajectory[0].cell_idx
        if cells_driven > 0:  # distance actually driven, missed exits included (D-2026-09-19-20)
            lc_per_km.append(lc / (cells_driven * CELL_LENGTH_M / 1000.0))

    delayed_20 = sum(1 for d in delays if d > 20.0)
    observation_period = sim_duration - warmup

    return {
        "num_completed": len(completed),
        "throughput_per_hour": len(completed) * 3600.0 / observation_period,
        "avg_travel_time": mean(tts),
        "avg_delay": mean(delays),
        "avg_lc_per_km": mean(lc_per_km),
        "pct_delayed_20s": delayed_20 / len(completed) * 100 if completed else 0.0,
    }
