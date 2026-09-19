"""Interactive Pygame playback of a finished run (extra `[viewer]`).

Controls:
    Space       Pause / Resume
    Up / Down   Increase / Decrease playback speed
    Left / Right  Scroll viewport
    +/-         Zoom in / out
    Home / End  Jump to start / end
    Click       Show vehicle info
    R           Reset viewport to follow traffic
    Q / Esc     Quit
"""

import logging
import subprocess
import sys
from typing import List, Optional, Tuple

import pygame

from odca.params import CELL_LENGTH_M, NetworkConfig
from odca.simulation.result import SimulationResult
from odca.viewer.snapshots import VehicleSnapshot, build_snapshots

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────────
# Colors
# ──────────────────────────────────────────────────────────────────────

BG_COLOR = (30, 30, 30)
ROAD_COLOR = (60, 60, 60)
LANE_LINE_COLOR = (180, 180, 180)
SHOULDER_COLOR = (100, 100, 100)
TEXT_COLOR = (220, 220, 220)
OVERLAY_BG = (20, 20, 20, 200)
RAMP_ON_COLOR = (31, 119, 180)
RAMP_OFF_COLOR = (214, 39, 40)
BLOCKED_COLOR = (255, 60, 60, 120)
INFO_BG = (40, 40, 50, 230)


def speed_to_color(speed: float, v_max: float) -> Tuple[int, int, int]:
    """Map speed to RGB: gray(stopped) -> red(slow) -> yellow -> green(fast).

    Args:
        speed: cells/s.
        v_max: the speed of full green (cells/s).
    """
    t = min(max(speed / v_max, 0.0), 1.0)
    if t < 0.33:
        # gray -> red
        s = t / 0.33
        return (
            int(136 + (214 - 136) * s),
            int(136 + (39 - 136) * s),
            int(136 + (40 - 136) * s),
        )
    elif t < 0.66:
        # red -> yellow
        s = (t - 0.33) / 0.33
        return (
            int(214 + (255 - 214) * s),
            int(39 + (127 - 39) * s),
            int(40 + (14 - 40) * s),
        )
    else:
        # yellow -> green
        s = (t - 0.66) / 0.34
        return (
            int(255 + (44 - 255) * s),
            int(127 + (160 - 127) * s),
            int(14 + (44 - 14) * s),
        )


# ──────────────────────────────────────────────────────────────────────
# Visualization
# ──────────────────────────────────────────────────────────────────────

class TrafficVisualizer:
    """Interactive Pygame traffic visualization."""

    # Layout constants
    LANE_HEIGHT = 36
    LANE_GAP = 2
    SHOULDER_HEIGHT = 8
    CELL_WIDTH_BASE = 18      # pixels per cell at zoom=1.0
    VEHICLE_HEIGHT = 28
    VEHICLE_LENGTH = 1        # cells (1 vehicle = 1 cell)
    HUD_HEIGHT = 48
    INFO_PANEL_W = 280
    MARGIN_TOP = 60

    SPEED_STEPS = [0.5, 1.0, 2.0, 5.0, 10.0, 20.0, 50.0]

    def __init__(self, snapshots: List[VehicleSnapshot], network: NetworkConfig,
                 sim_duration: float, v_max: float):
        """A player for `snapshots` on `network`.

        Args:
            snapshots: the vehicles' indexed trajectories.
            network: lanes, cells and ramp positions to draw.
            sim_duration: the end of the replay (s).
            v_max: the speed of the greenest colour (cells/s).
        """
        self.snapshots = snapshots
        self.num_lanes = network.num_lanes
        self.num_cells = network.num_cells
        self.sim_duration = sim_duration
        self.v_max = v_max
        self.onramp_cells = network.onramp_cells
        self.offramp_cells = network.offramp_cells

        # State
        self.sim_time = 0.0
        self.paused = False
        self.speed_idx = 3          # index into SPEED_STEPS → 5.0x
        self.zoom = 1.0
        self.viewport_x = 0.0      # leftmost cell in viewport
        self.auto_scroll = False
        self.selected_vehicle: Optional[VehicleSnapshot] = None

        # Window
        self.win_w = 1400
        self.win_h = (
            self.MARGIN_TOP
            + self.SHOULDER_HEIGHT
            + self.num_lanes * (self.LANE_HEIGHT + self.LANE_GAP) - self.LANE_GAP
            + self.SHOULDER_HEIGHT
            + self.HUD_HEIGHT
            + 20
        )

        pygame.init()
        pygame.display.set_caption("ODCA-DES Traffic Visualization")
        self.screen = pygame.display.set_mode(
            (self.win_w, self.win_h), pygame.RESIZABLE
        )
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("monospace", 14)
        self.font_sm = pygame.font.SysFont("monospace", 11)
        self.font_lg = pygame.font.SysFont("monospace", 18, bold=True)

    @classmethod
    def from_result(cls, result: SimulationResult) -> "TrafficVisualizer":
        """A player for a finished run.

        Args:
            result: the run to replay.
        """
        config = result.config
        return cls(build_snapshots(result.vehicles), config.network, config.sim_duration,
                   config.hdv_vehicle.v_max)

    @property
    def playback_speed(self) -> float:
        """Simulated seconds per real second."""
        return self.SPEED_STEPS[self.speed_idx]

    @property
    def cell_width(self) -> float:
        """Pixels per cell at the current zoom."""
        return self.CELL_WIDTH_BASE * self.zoom

    @property
    def road_top(self) -> int:
        """Screen y of the road's top edge."""
        return self.MARGIN_TOP + self.SHOULDER_HEIGHT

    @property
    def road_height(self) -> int:
        """Pixels from the first to the last lane."""
        return self.num_lanes * (self.LANE_HEIGHT + self.LANE_GAP) - self.LANE_GAP

    @property
    def visible_cells(self) -> int:
        """Cells across the window at the current zoom."""
        return int(self.win_w / self.cell_width) + 1

    def cell_to_x(self, cell_idx: int) -> float:
        """Convert cell index to screen x coordinate.

        Args:
            cell_idx: a cell.
        """
        return (cell_idx - self.viewport_x) * self.cell_width

    def lane_to_y(self, lane_idx: int) -> int:
        """Convert 1-based lane index to screen y (top of lane rect).

        Lane 1 (rightmost) at bottom, lane N at top.

        Args:
            lane_idx: a lane, 1 the rightmost.
        """
        row = self.num_lanes - lane_idx  # 0 = top
        return self.road_top + row * (self.LANE_HEIGHT + self.LANE_GAP)

    def screen_to_cell_lane(self, sx: int, sy: int) -> Optional[Tuple[int, int]]:
        """Convert screen coords to (cell_idx, lane_idx) or None.

        Args:
            sx: screen x.
            sy: screen y.
        """
        cell_idx = int(self.viewport_x + sx / self.cell_width)
        if cell_idx < 0 or cell_idx >= self.num_cells:
            return None
        for lane_idx in range(1, self.num_lanes + 1):
            y = self.lane_to_y(lane_idx)
            if y <= sy <= y + self.LANE_HEIGHT:
                return cell_idx, lane_idx
        return None

    # ── Drawing ──────────────────────────────────────────────────────

    def _draw_road(self):
        """Draw road surface, shoulders, lane dividers, ramps."""
        # Road surface
        pygame.draw.rect(
            self.screen, ROAD_COLOR,
            (0, self.road_top, self.win_w, self.road_height),
        )
        # Shoulders
        pygame.draw.rect(
            self.screen, SHOULDER_COLOR,
            (0, self.road_top - self.SHOULDER_HEIGHT,
             self.win_w, self.SHOULDER_HEIGHT),
        )
        pygame.draw.rect(
            self.screen, SHOULDER_COLOR,
            (0, self.road_top + self.road_height,
             self.win_w, self.SHOULDER_HEIGHT),
        )

        # Lane dividers (dashed)
        for i in range(1, self.num_lanes):
            y = self.road_top + i * (self.LANE_HEIGHT + self.LANE_GAP) - 1
            dash_len = 12
            gap_len = 8
            x = 0
            while x < self.win_w:
                pygame.draw.line(
                    self.screen, LANE_LINE_COLOR,
                    (x, y), (min(x + dash_len, self.win_w), y), 1,
                )
                x += dash_len + gap_len

        # Ramp markers
        for cell_idx in self.onramp_cells:
            sx = self.cell_to_x(cell_idx)
            if -20 < sx < self.win_w + 20:
                pygame.draw.line(
                    self.screen, RAMP_ON_COLOR,
                    (int(sx), self.road_top - self.SHOULDER_HEIGHT),
                    (int(sx), self.road_top + self.road_height + self.SHOULDER_HEIGHT),
                    2,
                )
                label = self.font_sm.render("ON", True, RAMP_ON_COLOR)
                self.screen.blit(label, (int(sx) + 3, self.road_top - self.SHOULDER_HEIGHT - 14))

        for cell_idx in self.offramp_cells:
            sx = self.cell_to_x(cell_idx)
            if -20 < sx < self.win_w + 20:
                pygame.draw.line(
                    self.screen, RAMP_OFF_COLOR,
                    (int(sx), self.road_top - self.SHOULDER_HEIGHT),
                    (int(sx), self.road_top + self.road_height + self.SHOULDER_HEIGHT),
                    2,
                )
                label = self.font_sm.render("OFF", True, RAMP_OFF_COLOR)
                self.screen.blit(label, (int(sx) + 3, self.road_top - self.SHOULDER_HEIGHT - 14))

    def _draw_distance_markers(self):
        """Draw km markers along the top."""
        # Show markers every 0.5 km or 1 km depending on zoom
        cells_per_km = 1000 / CELL_LENGTH_M
        step_km = 1.0 if self.zoom < 0.5 else 0.5
        step_cells = step_km * cells_per_km

        cell_start = int(self.viewport_x / step_cells) * step_cells
        cell = cell_start
        while cell <= self.viewport_x + self.visible_cells:
            sx = self.cell_to_x(int(cell))
            if 0 <= sx < self.win_w:
                km = cell * CELL_LENGTH_M / 1000
                label = self.font_sm.render(f"{km:.1f}km", True, (150, 150, 150))
                self.screen.blit(label, (int(sx) - label.get_width() // 2, 2))
                pygame.draw.line(
                    self.screen, (80, 80, 80),
                    (int(sx), 16), (int(sx), self.road_top - self.SHOULDER_HEIGHT),
                    1,
                )
            cell += step_cells

    def _draw_vehicles(self, active_positions: List[Tuple[VehicleSnapshot, int, int, float]]):
        """Draw vehicles: ovals for AVs, rectangles for HDVs (per dissertation convention).

        Args:
            active_positions: (snapshot, cell, lane, speed) of each vehicle on the road.
        """
        veh_w = max(4, int(self.VEHICLE_LENGTH * self.cell_width))
        veh_h = self.VEHICLE_HEIGHT
        y_offset = (self.LANE_HEIGHT - veh_h) // 2

        for snap, cell_idx, lane_idx, speed in active_positions:
            sx = self.cell_to_x(cell_idx)
            if sx + veh_w < 0 or sx > self.win_w:
                continue

            sy = self.lane_to_y(lane_idx) + y_offset
            color = speed_to_color(speed, self.v_max)
            rect = pygame.Rect(int(sx), sy, veh_w, veh_h)

            # Highlight selected
            if self.selected_vehicle and snap.vid == self.selected_vehicle.vid:
                highlight_rect = rect.inflate(4, 4)
                if snap.kind == "autonomous":
                    pygame.draw.ellipse(self.screen, (255, 255, 100), highlight_rect, 2)
                else:
                    pygame.draw.rect(self.screen, (255, 255, 100), highlight_rect, 2)

            if snap.kind == "autonomous":
                # AV = oval (per dissertation Figures 1-2)
                pygame.draw.ellipse(self.screen, color, rect)
            else:
                # HDV = rectangle (per dissertation Figures 1-2)
                pygame.draw.rect(self.screen, color, rect)

    def _draw_hud(self, n_active: int):
        """Draw heads-up display at bottom.

        Args:
            n_active: vehicles on the road now.
        """
        hud_y = self.win_h - self.HUD_HEIGHT
        pygame.draw.rect(
            self.screen, (20, 20, 20),
            (0, hud_y, self.win_w, self.HUD_HEIGHT),
        )
        pygame.draw.line(
            self.screen, (80, 80, 80),
            (0, hud_y), (self.win_w, hud_y), 1,
        )

        # Time
        t = self.sim_time
        time_str = f"t = {t:7.1f}s  ({t / 60:.1f} min)"
        self.screen.blit(
            self.font.render(time_str, True, TEXT_COLOR),
            (10, hud_y + 6),
        )

        # Playback
        state = "PAUSED" if self.paused else f"{self.playback_speed:.1f}x"
        color = (255, 200, 50) if self.paused else TEXT_COLOR
        self.screen.blit(
            self.font.render(f"Speed: {state}", True, color),
            (280, hud_y + 6),
        )

        # Vehicle count
        self.screen.blit(
            self.font.render(f"Vehicles: {n_active}", True, TEXT_COLOR),
            (480, hud_y + 6),
        )

        # Zoom
        self.screen.blit(
            self.font.render(f"Zoom: {self.zoom:.1f}x", True, TEXT_COLOR),
            (640, hud_y + 6),
        )

        # Controls hint
        hint = "Space:Pause  Arrows:Scroll  +/-:Zoom  Q:Quit"
        self.screen.blit(
            self.font_sm.render(hint, True, (120, 120, 120)),
            (10, hud_y + 28),
        )

        # Progress bar
        bar_x, bar_w = 750, self.win_w - 770
        bar_y, bar_h = hud_y + 10, 10
        pygame.draw.rect(self.screen, (50, 50, 50), (bar_x, bar_y, bar_w, bar_h))
        progress = min(self.sim_time / self.sim_duration, 1.0)
        pygame.draw.rect(
            self.screen, (80, 180, 80),
            (bar_x, bar_y, int(bar_w * progress), bar_h),
        )
        pct = self.font_sm.render(f"{progress * 100:.0f}%", True, TEXT_COLOR)
        self.screen.blit(pct, (bar_x + bar_w + 5, bar_y - 2))

    def _draw_speed_legend(self):
        """Draw color legend and shape key in top-right corner."""
        x0 = self.win_w - 200
        y0 = 4
        steps = 8
        box_w = 20
        box_h = 12
        for i in range(steps + 1):
            speed = self.v_max * i / steps
            color = speed_to_color(speed, self.v_max)
            pygame.draw.rect(self.screen, color, (x0 + i * box_w, y0, box_w, box_h))
        # Labels
        self.screen.blit(
            self.font_sm.render("0", True, (150, 150, 150)),
            (x0 - 8, y0 + box_h + 1),
        )
        km_h = self.v_max * CELL_LENGTH_M * 3.6
        self.screen.blit(
            self.font_sm.render(f"{km_h:.0f} km/h", True, (150, 150, 150)),
            (x0 + steps * box_w - 20, y0 + box_h + 1),
        )

        # Shape key: AV=oval, HDV=rect
        key_x = x0 - 140
        key_y = y0 + 2
        pygame.draw.ellipse(self.screen, (44, 160, 44), (key_x, key_y, 16, 10))
        self.screen.blit(
            self.font_sm.render("AV", True, (150, 150, 150)),
            (key_x + 20, key_y - 2),
        )
        pygame.draw.rect(self.screen, (44, 160, 44), (key_x + 50, key_y, 14, 10))
        self.screen.blit(
            self.font_sm.render("HDV", True, (150, 150, 150)),
            (key_x + 68, key_y - 2),
        )

    def _draw_vehicle_info(self):
        """Draw info panel for selected vehicle."""
        snap = self.selected_vehicle
        if snap is None:
            return
        pos = snap.at(self.sim_time)
        if pos is None:
            return

        cell_idx, lane_idx, speed = pos
        km = cell_idx * CELL_LENGTH_M / 1000
        km_h = speed * CELL_LENGTH_M * 3.6

        lines = [
            f"Vehicle #{snap.vid}",
            f"Type: {'AV' if snap.kind == 'autonomous' else 'HDV'}",
            f"Speed: {speed:.2f} cells/s ({km_h:.1f} km/h)",
            f"Cell: {cell_idx}  Lane: {lane_idx}",
            f"Position: {km:.2f} km",
        ]
        if snap.t_enter is not None:
            lines.append(f"Entered: {snap.t_enter:.1f}s")
        if snap.t_exit is not None:
            lines.append(f"Exited: {snap.t_exit:.1f}s")

        panel_w = self.INFO_PANEL_W
        panel_h = 18 * len(lines) + 16
        px = self.win_w - panel_w - 10
        py = self.road_top

        # Semi-transparent background
        panel_surf = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        panel_surf.fill(INFO_BG)
        self.screen.blit(panel_surf, (px, py))

        for i, line in enumerate(lines):
            color = (255, 220, 100) if i == 0 else TEXT_COLOR
            self.screen.blit(
                self.font_sm.render(line, True, color),
                (px + 8, py + 8 + i * 18),
            )

    # ── Event handling ───────────────────────────────────────────────

    def _handle_events(self) -> bool:
        """Process events. Returns False to quit."""
        scroll_speed = max(5, self.visible_cells // 4)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

            elif event.type == pygame.VIDEORESIZE:
                self.win_w = event.w
                self.win_h = event.h
                self.screen = pygame.display.set_mode(
                    (self.win_w, self.win_h), pygame.RESIZABLE
                )

            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_q, pygame.K_ESCAPE):
                    return False
                elif event.key == pygame.K_SPACE:
                    self.paused = not self.paused
                elif event.key == pygame.K_UP:
                    self.speed_idx = min(self.speed_idx + 1, len(self.SPEED_STEPS) - 1)
                elif event.key == pygame.K_DOWN:
                    self.speed_idx = max(self.speed_idx - 1, 0)
                elif event.key == pygame.K_RIGHT:
                    self.viewport_x = min(
                        self.viewport_x + scroll_speed,
                        self.num_cells - self.visible_cells,
                    )
                    self.auto_scroll = False
                elif event.key == pygame.K_LEFT:
                    self.viewport_x = max(self.viewport_x - scroll_speed, 0)
                    self.auto_scroll = False
                elif event.key in (pygame.K_PLUS, pygame.K_EQUALS, pygame.K_KP_PLUS):
                    self.zoom = min(self.zoom * 1.3, 10.0)
                elif event.key in (pygame.K_MINUS, pygame.K_KP_MINUS):
                    self.zoom = max(self.zoom / 1.3, 0.2)
                elif event.key == pygame.K_HOME:
                    self.sim_time = 0.0
                    self.viewport_x = 0.0
                elif event.key == pygame.K_END:
                    self.sim_time = self.sim_duration
                elif event.key == pygame.K_r:
                    self.auto_scroll = True
                    self.viewport_x = 0.0

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # left click
                    self._handle_click(event.pos)
                elif event.button == 4:  # scroll up
                    self.zoom = min(self.zoom * 1.1, 10.0)
                elif event.button == 5:  # scroll down
                    self.zoom = max(self.zoom / 1.1, 0.2)

        # Continuous key-hold scrolling
        keys = pygame.key.get_pressed()
        if keys[pygame.K_RIGHT]:
            self.viewport_x = min(
                self.viewport_x + scroll_speed * 0.3,
                max(0, self.num_cells - self.visible_cells),
            )
            self.auto_scroll = False
        if keys[pygame.K_LEFT]:
            self.viewport_x = max(self.viewport_x - scroll_speed * 0.3, 0)
            self.auto_scroll = False

        return True

    def _handle_click(self, pos: Tuple[int, int]):
        """Handle mouse click — select vehicle under cursor.

        Args:
            pos: the clicked screen point.
        """
        mx, my = pos

        # Check progress bar click
        hud_y = self.win_h - self.HUD_HEIGHT
        bar_x, bar_w = 750, self.win_w - 770
        bar_y, bar_h = hud_y + 10, 10
        if bar_x <= mx <= bar_x + bar_w and bar_y - 5 <= my <= bar_y + bar_h + 5:
            frac = (mx - bar_x) / bar_w
            self.sim_time = frac * self.sim_duration
            return

        # Find vehicle at click position
        result = self.screen_to_cell_lane(mx, my)
        if result is None:
            self.selected_vehicle = None
            return

        click_cell, click_lane = result

        # Find nearest vehicle within a few cells
        best = None
        best_dist = 999
        for snap in self.snapshots:
            p = snap.at(self.sim_time)
            if p is None:
                continue
            cell_idx, lane_idx, speed = p
            if lane_idx != click_lane:
                continue
            dist = abs(cell_idx - click_cell)
            if dist < 6 and dist < best_dist:
                best = snap
                best_dist = dist

        self.selected_vehicle = best

    # ── Main loop ────────────────────────────────────────────────────

    def run(self):
        """Main visualization loop."""
        fps = 60
        running = True

        while running:
            dt = self.clock.tick(fps) / 1000.0  # real seconds

            running = self._handle_events()

            # Advance simulation time
            if not self.paused and self.sim_time < self.sim_duration:
                self.sim_time += dt * self.playback_speed
                self.sim_time = min(self.sim_time, self.sim_duration)

            # Gather active vehicles
            active = []
            for snap in self.snapshots:
                pos = snap.at(self.sim_time)
                if pos is not None:
                    active.append((snap, pos[0], pos[1], pos[2]))

            # Draw
            self.screen.fill(BG_COLOR)
            self._draw_distance_markers()
            self._draw_road()
            self._draw_vehicles(active)
            self._draw_speed_legend()
            self._draw_hud(len(active))
            self._draw_vehicle_info()

            pygame.display.flip()

        pygame.quit()

    def record(self, output_path: str, playback_speed: float = 5.0,
               fps: int = 30, scroll_speed: float = 0.5):
        """Record the visualization to an MP4 file via ffmpeg.

        Args:
            output_path: Path to output MP4 file.
            playback_speed: Simulation seconds per real second.
            fps: Output video frame rate.
            scroll_speed: Viewport auto-scroll speed (cells per sim-second).
        """
        sim_dt = playback_speed / fps  # sim-seconds per frame
        self.paused = False
        self.sim_time = 0.0
        self.viewport_x = 0.0
        self.auto_scroll = True

        # Start ffmpeg process
        cmd = [
            "ffmpeg", "-y",
            "-f", "rawvideo",
            "-vcodec", "rawvideo",
            "-s", f"{self.win_w}x{self.win_h}",
            "-pix_fmt", "rgb24",
            "-r", str(fps),
            "-i", "-",
            "-c:v", "libx264",
            "-preset", "medium",
            "-crf", "23",
            "-pix_fmt", "yuv420p",
            output_path,
        ]
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        logger.info(f"Recording to {output_path} at {fps} fps, "
                    f"{playback_speed}x speed...")

        total_frames = int(self.sim_duration / sim_dt)
        frame_count = 0

        while self.sim_time < self.sim_duration:
            # Auto-scroll viewport to follow traffic
            if self.auto_scroll:
                target_x = self.sim_time * scroll_speed
                max_x = max(0, self.num_cells - self.visible_cells)
                self.viewport_x = min(target_x, max_x)

            # Gather active vehicles
            active = []
            for snap in self.snapshots:
                pos = snap.at(self.sim_time)
                if pos is not None:
                    active.append((snap, pos[0], pos[1], pos[2]))

            # Draw
            self.screen.fill(BG_COLOR)
            self._draw_distance_markers()
            self._draw_road()
            self._draw_vehicles(active)
            self._draw_speed_legend()
            self._draw_hud(len(active))

            pygame.display.flip()

            # Capture frame
            frame_data = pygame.image.tostring(self.screen, "RGB")
            proc.stdin.write(frame_data)

            self.sim_time += sim_dt
            frame_count += 1
            if frame_count % (fps * 5) == 0:
                pct = 100 * self.sim_time / self.sim_duration
                logger.info(f"  Recording: {pct:.0f}% ({frame_count}/{total_frames} frames)")

            # Allow quit during recording
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    break
                if event.type == pygame.KEYDOWN and event.key == pygame.K_q:
                    break

        proc.stdin.close()
        proc.wait()
        pygame.quit()
        logger.info(f"Video saved to {output_path} ({frame_count} frames)")
