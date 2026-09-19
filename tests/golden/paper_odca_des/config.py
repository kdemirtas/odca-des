"""Configuration for ODCA-DES experiments.

All parameters in one place for reproducibility. Units:
  - speed: cells/s (continuous float)
  - time: seconds
  - distance: cells (1 cell = CELL_LENGTH_M meters)
"""

import logging
from dataclasses import dataclass, field
from typing import List, Optional, Tuple


CELL_LENGTH_M = 7.5  # meters per cell


@dataclass
class VehicleParams:
    """Behavioral parameters for a vehicle type.

    For HDVs, tau, action_interval, and slowdown_prob are *mean* values;
    per-driver values are sampled at vehicle creation (see generator.py).
    For AVs, these are used as-is (deterministic).
    """
    tau: float              # reaction time / delayed release — mean (s)
    tau_std: float          # std dev for per-driver tau sampling (0 = deterministic)
    standstill_spacing: float  # minimum spacing (cells), typically 1.0
    v_max: float            # maximum speed (cells/s)
    slowdown_prob: float    # random slowdown probability — mean (0 for AV)
    slowdown_prob_std: float  # std dev for per-driver slowdown_prob sampling
    slowdown_delta: float   # speed reduction on slowdown (cells/s)
    action_interval: float  # driver re-evaluation interval — mean (s)
    action_interval_std: float  # std dev for per-driver action_interval sampling
    # Lane change parameters
    mlc_k: float            # MLC logistic steepness
    mlc_r0: float           # MLC logistic midpoint
    dlc_k: float            # DLC logistic steepness
    dlc_v0: float           # DLC speed threshold (cells/s)
    dlc_cooldown: float     # minimum time between DLCs (s)
    # Safety
    safety_gap_front: float # min front gap for LC (cells)
    safety_gap_rear: float  # min rear gap for LC (cells)
    look_ahead: int         # cells to scan forward
    look_behind: int        # cells to scan backward
    # Optional
    dlc_enabled: bool = True  # whether DLC is active (False for centrally controlled AVs)


HDV_PARAMS = VehicleParams(
    tau=1.5,
    tau_std=0.3,
    standstill_spacing=1.0,
    v_max=5.2,        # 5.2 cells/s = 140.4 km/h (87 mph) at 7.5m cells
    slowdown_prob=0.15,
    slowdown_prob_std=0.05,
    slowdown_delta=0.5,
    action_interval=1.0,
    action_interval_std=0.2,
    mlc_k=8.0,
    mlc_r0=0.3,
    dlc_k=3.0,
    dlc_v0=1.0,       # speed advantage threshold for DLC (cells/s)
    dlc_cooldown=10.0,
    safety_gap_front=2.0,
    safety_gap_rear=2.0,
    look_ahead=10,
    look_behind=10,
)

AV_PARAMS = VehicleParams(
    tau=0.5,
    tau_std=0.0,
    standstill_spacing=1.0,
    v_max=5.2,
    slowdown_prob=0.0,
    slowdown_prob_std=0.0,
    slowdown_delta=0.0,
    action_interval=0.5,
    action_interval_std=0.0,
    mlc_k=8.0,
    mlc_r0=0.3,
    dlc_k=5.0,
    dlc_v0=0.4,       # AVs more sensitive to speed advantage
    dlc_cooldown=3.0,
    dlc_enabled=False,  # centrally controlled — no discretionary lane changes
    safety_gap_front=1.0,
    safety_gap_rear=1.0,
    look_ahead=12,
    look_behind=12,
)


@dataclass
class ODFlow:
    """Origin-destination flow specification.

    Supports two modes:
      1. Single destination: ODFlow("mainline", 300, 1500.0)
      2. Destination distribution: ODFlow("mainline_lane_1", flow_rate=1500.0,
             destinations=[(300, 0.20), (550, 0.25), (800, 0.55)])
         Each tuple is (destination_cell_idx, probability). Probabilities
         must sum to 1.0. The generator samples a destination per vehicle.
    """
    origin_id: str             # "mainline_lane_1", "onramp_1", etc.
    destination_cell: int = -1 # single destination (legacy mode; -1 = unused)
    flow_rate: float = 0.0     # vehicles per hour
    destinations: Optional[List[Tuple[int, float]]] = None  # [(cell_idx, prob), ...]


@dataclass
class NetworkConfig:
    """Freeway network geometry."""
    num_lanes: int = 4
    num_cells: int = 800       # 800 cells × 7.5m = 6 km
    speed_limit: float = 5.2   # cells/s
    onramp_cells: List[int] = field(default_factory=lambda: [100, 400])
    offramp_cells: List[int] = field(default_factory=lambda: [300, 550, 750])


@dataclass
class SimConfig:
    """Full simulation configuration."""
    network: NetworkConfig = field(default_factory=NetworkConfig)
    hdv_params: VehicleParams = field(default_factory=lambda: HDV_PARAMS)
    av_params: VehicleParams = field(default_factory=lambda: AV_PARAMS)
    av_penetration: float = 0.0
    sim_duration: float = 3600.0   # seconds
    warmup: float = 300.0          # seconds before collecting stats
    seed: int = 42
    av_controller_dt: float = 0.1  # central AV controller update interval (s)
    log_level: int = logging.INFO
    od_flows: List[ODFlow] = field(default_factory=lambda: [
        # --- Mainline: 6000 veh/h total, 1500 veh/h per lane ---
        # Off-ramp exits: 300 (ramp 1), 550 (ramp 2), 750 (ramp 3)
        # End-of-segment exit: 800
        ODFlow("mainline_lane_1", flow_rate=1500.0, destinations=[
            (300, 0.20), (550, 0.25), (750, 0.15), (800, 0.40),
        ]),
        ODFlow("mainline_lane_2", flow_rate=1500.0, destinations=[
            (300, 0.10), (550, 0.15), (750, 0.10), (800, 0.65),
        ]),
        ODFlow("mainline_lane_3", flow_rate=1500.0, destinations=[
            (300, 0.05), (550, 0.10), (750, 0.05), (800, 0.80),
        ]),
        ODFlow("mainline_lane_4", flow_rate=1500.0, destinations=[
            (300, 0.02), (550, 0.05), (750, 0.03), (800, 0.90),
        ]),
        # --- On-ramps ---
        ODFlow("onramp_1", flow_rate=500.0, destinations=[
            (550, 0.50), (750, 0.20), (800, 0.30),
        ]),
        ODFlow("onramp_2", flow_rate=500.0, destinations=[
            (750, 0.30), (800, 0.70),
        ]),
    ])
