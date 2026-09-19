"""Matplotlib views of a finished run (extra `[viewer]`): an animation of the road and a
time-space diagram per lane."""

import logging
from typing import Optional, Tuple

import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FuncAnimation
from matplotlib.collections import LineCollection

from odca.params import CELL_LENGTH_M
from odca.simulation.result import SimulationResult
from odca.viewer.snapshots import build_snapshots, reconstruct_grid

logger = logging.getLogger(__name__)


def _traffic_cmap():
    """Grey (stopped), red, orange, green (top speed)."""
    return mcolors.LinearSegmentedColormap.from_list(
        "traffic", ["#888888", "#d62728", "#ff7f0e", "#2ca02c"], N=256)


def _upscale_grid(grid: np.ndarray, row_height: int, col_width: int) -> np.ndarray:
    """Repeat each cell into a (row_height x col_width) block for visibility.

    Args:
        grid: speeds per (lane row, cell).
        row_height: pixels per lane.
        col_width: pixels per cell.
    """
    return np.repeat(np.repeat(grid, row_height, axis=0), col_width, axis=1)


def _draw_lane_dividers(ax, num_lanes: int, row_height: int, width: int):
    """Draw white lines between lanes.

    Args:
        ax: the axes.
        num_lanes: lanes drawn.
        row_height: pixels per lane.
        width: pixels across.
    """
    for i in range(1, num_lanes):
        y = i * row_height - 0.5
        ax.axhline(y, color="white", lw=2)


def animate_result(result: SimulationResult, fps: float = 10, playback_speed: float = 5.0,
                   cell_window: Optional[int] = None, save_path: Optional[str] = None):
    """Show or save a bird's-eye animation of a run, cells coloured by speed.

    Args:
        result: the run.
        fps: frames per second.
        playback_speed: simulated seconds per real second.
        cell_window: cells shown from the start of the road (None: all).
        save_path: `.gif` or a video file; None shows the window.
    """
    config = result.config
    network = config.network
    snapshots = build_snapshots(result.vehicles)
    num_lanes, num_cells = network.num_lanes, network.num_cells
    sim_duration, v_max = config.sim_duration, config.hdv_vehicle.v_max
    onramp_cells, offramp_cells = network.onramp_cells, network.offramp_cells
    dt = playback_speed / fps  # sim-seconds per frame
    times = np.arange(0, sim_duration, dt)

    # Viewing window
    window = cell_window or num_cells
    cell_lo = 0

    # Upscale: each cell becomes (row_height x col_width) pixels
    row_height = 20
    col_width = 3

    # Colormap: gray (stopped) -> red (slow) -> yellow -> green (v_max)
    cmap = _traffic_cmap()
    cmap.set_bad(color=(0.93, 0.93, 0.93, 1.0))  # empty cells: light gray
    norm = mcolors.Normalize(vmin=0, vmax=v_max)

    # Figure setup
    disp_w = window * col_width
    disp_h = num_lanes * row_height
    fig_w = min(20, max(12, disp_w / 80))
    fig_h = max(3.0, disp_h / 40 + 1.5)
    fig, ax = plt.subplots(figsize=(fig_w, fig_h))

    grid0 = reconstruct_grid(snapshots, 0, num_lanes, num_cells)
    view = np.ma.masked_invalid(grid0[:, cell_lo:cell_lo + window])
    upscaled = _upscale_grid(view, row_height, col_width)

    im = ax.imshow(
        upscaled, aspect="auto", interpolation="nearest",
        cmap=cmap, norm=norm,
    )

    _draw_lane_dividers(ax, num_lanes, row_height, disp_w)

    # Mark ramps
    if onramp_cells:
        for c in onramp_cells:
            if cell_lo <= c < cell_lo + window:
                x = (c - cell_lo) * col_width
                ax.axvline(x, color="#1f77b4", lw=1.5, ls="--", alpha=0.6)
    if offramp_cells:
        for c in offramp_cells:
            if cell_lo <= c < cell_lo + window:
                x = (c - cell_lo) * col_width
                ax.axvline(x, color="#d62728", lw=1.5, ls="--", alpha=0.6)

    # Lane labels
    lane_labels = [f"L{num_lanes - i}" for i in range(num_lanes)]
    lane_centers = [i * row_height + row_height // 2 for i in range(num_lanes)]
    ax.set_yticks(lane_centers)
    ax.set_yticklabels(lane_labels)

    # X-axis in km
    xtick_step = max(1, window // 10) * col_width
    xticks = list(range(0, disp_w, xtick_step))
    ax.set_xticks(xticks)
    ax.set_xticklabels(
        [f"{(cell_lo + x // col_width) * CELL_LENGTH_M / 1000:.1f}" for x in xticks]
    )
    ax.set_xlabel("Position (km)")

    title = ax.set_title("t = 0.0 s", fontsize=12, fontweight="bold")
    fig.colorbar(im, ax=ax, label="Speed (cells/s)", shrink=0.8, pad=0.02)

    count_text = ax.text(
        0.01, 1.02, "", transform=ax.transAxes, fontsize=9,
        verticalalignment="bottom",
    )

    fig.tight_layout()

    def update(frame_idx):

        """Draw one frame; return the changed artists.

            Args:
                frame_idx: index into the frame times.
            """
        t = times[frame_idx]
        grid = reconstruct_grid(snapshots, t, num_lanes, num_cells)
        view = np.ma.masked_invalid(grid[:, cell_lo:cell_lo + window])
        upscaled = _upscale_grid(view, row_height, col_width)
        im.set_data(upscaled)

        title.set_text(f"t = {t:.1f} s")
        n_active = np.count_nonzero(~np.isnan(grid))
        count_text.set_text(f"Vehicles: {n_active}")

        return [im, title, count_text]

    anim = FuncAnimation(
        fig, update, frames=len(times),
        interval=1000 / fps, blit=True,
    )

    if save_path:
        logger.info(f"Saving animation to {save_path} ({len(times)} frames)...")
        if save_path.endswith(".gif"):
            anim.save(save_path, writer="pillow", fps=fps)
        else:
            anim.save(save_path, writer="ffmpeg", fps=fps, dpi=120)
        logger.info(f"Saved: {save_path}")
    else:
        plt.show()

    plt.close(fig)


def plot_trajectories(result: SimulationResult, lane_filter: Optional[int] = None,
                      t_range: Optional[Tuple[float, float]] = None,
                      save_path: Optional[str] = None):
    """Time-space diagram per lane, trajectories coloured by speed.

    Args:
        result: the run.
        lane_filter: one lane to draw; None draws every lane, lane 1 at the bottom.
        t_range: (start, end) seconds to draw; None draws the whole run.
        save_path: file to write; None shows the window.
    """
    config = result.config
    num_lanes = config.network.num_lanes
    cmap, norm = _traffic_cmap(), mcolors.Normalize(vmin=0, vmax=config.hdv_vehicle.v_max)
    lanes = [lane_filter] if lane_filter is not None else list(range(num_lanes, 0, -1))
    height = 6.0 if len(lanes) == 1 else 3.0 * len(lanes)
    fig, axes = plt.subplots(len(lanes), 1, figsize=(14, height), sharex=True, sharey=True,
                             squeeze=False)
    axes = list(axes[:, 0])
    km = CELL_LENGTH_M / 1000
    for ax, lane_idx in zip(axes, lanes):
        segments, speeds = [], []
        for vehicle in result.vehicles:
            for a, b in zip(vehicle.trajectory, vehicle.trajectory[1:]):
                in_time = t_range is None or t_range[0] <= a.time <= t_range[1]
                if a.lane_idx == lane_idx == b.lane_idx and in_time:
                    segments.append([(a.time, a.cell_idx * km), (b.time, b.cell_idx * km)])
                    speeds.append(a.speed)
        lines = LineCollection(segments, cmap=cmap, norm=norm, linewidths=0.8)
        lines.set_array(np.array(speeds))
        ax.add_collection(lines)
        ax.autoscale()
        ax.set_ylabel(f"Lane {lane_idx}\nPosition (km)")
    axes[-1].set_xlabel("Time (s)")
    title = "Time-Space Diagram" + (f" (Lane {lane_filter})" if lane_filter is not None else "")
    fig.suptitle(title, fontsize=13, fontweight="bold")
    fig.subplots_adjust(hspace=0.15, top=0.94, right=0.88)
    fig.colorbar(plt.cm.ScalarMappable(cmap=cmap, norm=norm),
                 cax=fig.add_axes([0.9, 0.15, 0.015, 0.7]), label="Speed (cells/s)")
    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches="tight")
        logger.info(f"Saved trajectory plot: {save_path}")
    else:
        plt.show()
    plt.close(fig)
