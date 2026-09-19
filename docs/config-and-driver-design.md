# Config pattern and driver split

Design for HANDOVER N2 to N4. Decisions D-2026-09-19-23 (configs) and D-2026-09-19-24 (driver).

## Configs: one schema per class, ConfigMixin

All schemas are plain dataclasses in `odca/params.py`. A class names its schema and takes one
config; runtime objects (env, RNG streams, cells, its vehicle) are separate arguments.

```python
# odca/params.py
@dataclass(frozen=True, slots=True)
class HumanDriverConfig:
    tau: float = 1.5                 # reaction time, mean (s)
    tau_std: float = 0.3
    action_interval: float = 1.0
    action_interval_std: float = 0.2
    slowdown_prob: float = 0.1
    slowdown_prob_std: float = 0.05
    slowdown_delta: float = 1.0
    lane_change: LaneChangeConfig = field(default_factory=LaneChangeConfig)
    lc_patience: float = 3.0         # was Vehicle._LC_PATIENCE
    min_reeval_ratio: float = 0.5    # was Vehicle._MIN_REEVAL_RATIO

class ConfigMixin:
    Config: ClassVar[type]

    @classmethod
    def from_config(cls, cfg, **runtime):
        """dict, YAML or dataclass in; omegaconf checks types and unknown keys; dataclass out."""
        merged = OmegaConf.merge(OmegaConf.structured(cls.Config), cfg)
        return cls(OmegaConf.to_object(merged), **runtime)

# odca/entity/driver.py
class HumanDriver(Driver):
    Config = HumanDriverConfig
    def __init__(self, cfg: HumanDriverConfig, traits: DriverTraits, streams: DriverStreams): ...
```

omegaconf runs once per run, where the `SimConfig` is loaded and merged (YAML, CLI overrides, a
paper's values). Everything created inside the run gets frozen dataclasses. The reason is speed:
a DictConfig attribute read measured about 9 µs against 0.04 µs for a dataclass slot (about 250 times slower), and a driver reads its
parameters millions of times per run.

Population versus individual: a config holds population values (the means and spreads).
`DriverTraits` holds one driver's values (tau, action interval, slowdown probability), sampled
once at creation by the one sampler (N3). So the config is never copied per vehicle.

## Driver split

| | Vehicle | Driver |
|---|---|---|
| owns | cell label, cell lock, delayed release, forward and lateral moves, exit, trajectory, route | target speed, direction, lane-change curves, gap acceptance, decision state |
| process | movement process (every vehicle) | `HumanDriver`: its own; `AutonomousDriver`: none, called by `AutonomousController` |
| config | `VehicleConfig` (v_max, standstill spacing) | `HumanDriverConfig`, `AutonomousDriverConfig` |

The link contract (Kerem agreed, 2026-09-19; widened as built, D-2026-09-19-30):

| direction | allowed |
|---|---|
| driver to vehicle | read state (cell, speed, fractional position, route, last lane-change time, `cfg`); neighbours through cells (leader here or in the next lane); commands: `set_target_speed`, `request_direction` |
| vehicle to driver | `wake()` after a neighbour moved or freed a cell; `react_now()` after a speed-limit change; `accepts_gap(cell)`, `sees_blockage()`, `evaluate_direction()` when stopped at a blockage; read `tau` (delayed release), `action_interval` (retry wait when blocked), `lc_patience`, `merge_priority()` |

As built (N4): `Vehicle(env, cfg, driver, origin_cell, destination)`; `HumanDriver(cfg, streams,
traits)`; `AutonomousDriver(cfg, streams, controller)` registers itself; `VehicleFactory.build
(autonomous, origin_cell, destination)` is the one construction path. Counters: the vehicle
counts moves (lane changes, patience failures, missed exits), the driver counts decisions
(slowdowns, car-following and speed evaluations, gap rejections); `lc_failures` in the results
sums patience failures and gap rejections.

A driver never writes a vehicle field. The reaction-time release stays in `Vehicle`, because it
is the mechanism the paper describes; it reads tau from the driver.

The type switches disappear: `vehicle.vtype == HDV` becomes the driver's class, `dlc_enabled` stays
a driver config field (a parameter, not a type switch), `HDV` and `AV` classes go; reporting
code reads `vehicle.kind`.

## Not now

- Controllers per road segment (BACKLOG B5): a roadside-unit model feature. Not a speed-up: SimPy
  runs on one thread, and the work is one decision per AV per tick however it is split.
- Own event loop instead of SimPy (BACKLOG B6, a v2 option).
