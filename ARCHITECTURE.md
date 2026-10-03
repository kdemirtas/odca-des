# ARCHITECTURE: odca-des
> **Owned by `/architect`. Two pages max. Last updated 2026-10-03.** Code follows this file; when
> they disagree, either the code is wrong or this file is, and a `DECISIONS.md` entry says which.

## Purpose
One discrete-event cellular-automaton traffic simulator (ODCA-DES) shared by every ODCA paper. A
bug is fixed once, here. A capability one paper needs (platooning, lane-change logging) is added
here, switched off by default, so it never moves another paper's numbers; each paper's golden
fingerprint is a test in this repo that proves it. MIT licensed, published with the first paper.

## Boundaries
Modules, what each owns, and what it may import. A module not listed here does not exist yet;
`/architect` adds it before code does.

| Module | Owns | May import | Never imports |
|---|---|---|---|
| `odca/params.py`, `odca/configs/*.yaml` | `ConfigMixin`, `validate` and `to_yaml`, the one way a config becomes YAML (YAML with file references, `odca://` defaults, `_base_` overrides, `model` picks a family member); every config schema of the ODCA model (the NaSch baseline keeps its own `NaSchConfig`, since it imports nothing from `odca`); `CELL_LENGTH_M`; the published vehicle, driver and controller defaults as YAML (D-2026-09-19-23) | stdlib, omegaconf | any other `odca` module, any paper |
| `odca/rng.py` | `RNGRegistry`: one `SeedSequence` stream per source | numpy | any other `odca` module |
| `odca/models/` | Newell, MLC and DLC probabilities; pure functions | stdlib | simpy, any `odca` module |
| `odca/infrastructure/` | `Cell` and its endpoint subclasses `OriginCell`, `DestinationCell`; `Lane`; `Freeway` with its named `Origin`s and `Destination`s; `Incident` (D-2026-09-19-26 to -28) | simpy, params | entity, simulation |
| `odca/entity/` | `Vehicle` (physical: cell label, lock, movement, trajectory), `Driver`, `HumanDriver`, `AutonomousDriver`, `DriverStreams`, `DriverTraits` and `TraitSampler` (`driver.py`), `AutonomousController` (`controller.py`), `TrajectoryRecord` (D-2026-09-19-24, -30) | infrastructure, models, params, rng (`DriverStreams.spawn`, `TraitSampler.spawn`) | simulation, analysis, experiment |
| `odca/simulation/` | `Simulation`, `VehicleGenerator`, `VehicleFactory` (the one place a vehicle is built with its driver), `SimulationResult` and `RunCounters` (`result.py`, D-2026-09-19-32), RNG stream order | entity, infrastructure, rng, params | analysis, experiment, viewer |
| `odca/analysis/` | Edie FD, passage-time flow, `summary_statistics`; `mean_ci95` in `intervals.py`, the only interval code (D-2026-09-19-33) | entity (read-only), params | simulation, experiment |
| `odca/baselines/` | NaSch | numpy | the rest of `odca` |
| `odca/experiment/` | `RunRecord`, `run_once` (simulate, time, measure), per-seed JSON writer and strict reader (`records.py`), aggregation into the CSV schema below (`tables.py`) (D-2026-09-19-33) | simulation, analysis, params | viewer, any paper |
| `odca/viewer/` | `snapshots.py` (trajectories indexed by time), `animation.py` (matplotlib animation, time-space diagram), `playback.py` (pygame); each takes a `SimulationResult`; extra `[viewer]` (D-2026-09-19-34) | simulation, entity, params | experiment |
| `tests/` | unit tests; `tests/golden/<paper>/` scenario definitions and `fingerprint.json` per paper | everything in `odca` | a paper repo (fixtures are copied in, not imported) |

Papers keep: parameter values (`config.py`), scenario definitions, figure scripts, diagnostics. They import `odca`; nothing in `odca` imports a paper.

## Layout

    odca/            the package (import name odca)
    tests/           unit tests; tests/golden/<paper>/ = config.py, configs/*.yaml, scenarios.py, fingerprint.json per paper (paper_lc_logistic also models/)
    docs/            longer reference docs ARCHITECTURE.md links
    pyproject.toml   distribution odca-des, extra [viewer], dev group pytest

## Data contracts
Every artifact that crosses a module boundary or leaves the project: its grain, its writer, its
readers, and where the contract is asserted. "Nowhere" is a legal entry and a backlog item.

| Artifact | Grain (key) | Written by | Read by | Asserted in |
|---|---|---|---|---|
| per-seed JSON | (scenario, AV share, hdv_action_interval, seed); keys label, av_penetration, seed, hdv_action_interval, av_action_interval, stats, counters, plus the paper's extra keys; all seven are required (D-2026-10-02-3) | `odca.experiment.write_run` | `odca.experiment.read_runs` (a duplicate run, or a file with a key missing, is refused) | `tests/test_experiment.py` |
| aggregate CSV | (scenario, av_penetration, hdv_action_interval, metric): n, mean, std, ci95_lo, ci95_hi, six decimals | `odca.experiment.write_aggregate_csv` | paper figure scripts, manuscript tables | `tests/test_experiment.py` |
| `tests/golden/<paper>/fingerprint.json` | run id `<scenario>_seed<n>` in quick mode: 12 stats over every vehicle of the run (D-2026-09-22-2) and 9 counters | `uv run pytest tests/test_golden.py --write-golden`, only under a decision | the golden test | the golden test, exact match |

## Core types
The concepts the code passes around. Each has one definition; functions take the type, not its
fields.

| Type | Meaning | Defined in |
|---|---|---|
| `VehicleConfig`, `HumanDriverConfig`, `AutonomousDriverConfig`, `ControllerConfig` | one class's parameters each, population values (means and spreads for humans); validated by omegaconf once per run, frozen dataclasses after | `odca/params.py`. Lane-change models are a family: `BaseLaneChangeConfig` (gaps, cooldown, and the one switch `dlc_requires_advantage`: off by default, on in paper-odca-des, deleted at the last paper's switch-over, D-2026-09-22-1, D-2026-10-02-1), `LogisticLaneChangeConfig`. `look_ahead` is the forward range and `look_behind` the rear one (D-2026-10-02-2). The movement resolution and escape speed are `VehicleConfig` fields, the decision constants (patience, re-evaluation ratio, blockage scan, creep and slowdown floors) `DriverConfig` fields (D-2026-09-19-30) |
| `DriverTraits` | one driver's sampled values (tau, action interval, slowdown probability), drawn once at creation by `TraitSampler` | `odca/entity/driver.py` |
| `SimConfig`, `NetworkConfig`, `ODFlow`, `Destination` | one run: geometry, demand, the two vehicle types, AV penetration, seed, duration, warm-up; values come from the paper's YAML | `odca/params.py` |
| `Cell`, `Lane`, `Freeway` | the spatial resources; a cell's neighbour links are set when the road is built, reshaping a road relinks it (`Lane.make_periodic`, D-2026-09-19-35) | `odca/infrastructure/` |
| `Origin`, `Destination` (with `OriginCell`, `DestinationCell`) | named places where trips start and end, declared in the network config; an endpoint cell is transparent unless given a speed limit, which meters inflow or throttles outflow | `odca/infrastructure/` (D-2026-09-19-26, -27) |
| demand table, `IncidentConfig` | veh/h per (origin, destination) name pair, one generator per pair; incidents block or slow cells for a time, then restore them | `odca/params.py`, `odca/infrastructure/incident.py` (D-2026-09-19-26, -28) |
| `Vehicle` | one vehicle's physical side: position label, cell lock with delayed release (reads tau from its driver), movement, exit, trajectory, move counters; `kind` names its driver's kind | `odca/entity/vehicle.py` |
| `Driver` (`HumanDriver`, `AutonomousDriver`) | the decisions: target speed, direction, lane-change curves, gap acceptance, exposure since the last decision, decision counters. `HumanDriver` runs its own SimPy process; `AutonomousDriver` registers with an `AutonomousController`, which decides for it every `dt`. A new behaviour is a subclass overriding `decide`, `evaluate_speed` or `evaluate_direction` | `odca/entity/driver.py` |
| `TrajectoryRecord` | one T(x, n) passage record: the cell, the lane, the speed, the free-flow speed of that cell, and both of the protocol's stamps, `acquired` (T_acq) and `time` (T_arr), so lock time, queueing time and crossing time are all read off the trajectory rather than kept as state (D-2026-09-20-5) | `odca/entity/vehicle.py` |
| lane-change model of a run | the type of the human `lane_change` config picks the driver class: a `HumanDriver` subclass registers for a family member through `lane_change_config`, `HumanDriver.class_for` looks it up: `HumanDriver` for the logistic model, an error for an unregistered one (D-2026-10-03-3) | `odca/entity/driver.py`; used by `odca/simulation/factory.py` |
| `LaneChangeRecord`, `LaneChangeReason` | one lane change that happened: time, cell left, from lane, to lane, and why (blockage, destination, discretionary); kept on `Vehicle.lane_changes`, always written (D-2026-10-03-1) | `odca/entity/vehicle.py` |
| `SpaceTimeRegion` | the cells, lanes and time span Edie's definitions are taken over; `edie_fd_points` takes it whole (D-2026-10-02-5) | `odca/analysis/metrics.py` |
| `SimulationResult`, `RunCounters` | one run: the validated config it ran with (`config_yaml()` reruns it), every vehicle, the generated count, the event counters; completed and still-active vehicles are derived. The counters keep the split: the vehicle's moves (`lane_changes`, `lc_patience_failures`, `missed_exits`) and the driver's decisions (`gap_rejections`, `slowdowns`, `cf_evaluations`, `speed_evaluations`), plus the controller's and SimPy's. `lc_failures` is a derived property, not a stored key (D-2026-09-20-12) | `odca/simulation/result.py` (D-2026-09-19-32) |

## Invariants
What must hold after every run, each with the check that proves it.

1. **One vehicle per cell.** `Cell.resource` has capacity 1, and a vehicle that has locked a cell another is still crossing out of waits at the boundary until that one has left, so no vehicle arrives in a cell another has not left (D-2026-10-02-6, `docs/cell-overlap.md`). Checked by `tests/test_invariants.py`.
2. **Headway by delayed release.** A cell is released tau seconds after its vehicle takes the next one (`_delayed_release`, `_exit`), so two vehicles pass a road cell no closer than tau + d / v_max = 1.692 s at HDV defaults, a floor of 2127 veh/h. Checked by `tests/test_invariants.py`. The floor is not the flow a lane carries: a saturated single lane measured about 1,350 veh/h (BACKLOG B15).
3. **Same config and seed, same numbers.** `Simulation` spawns its streams in a fixed order: three decision streams (`DriverStreams`), three trait streams (`TraitSampler`), then one per OD pair in demand-table order, then `initial_vehicle_type`. A new stream goes last, or every number moves. Checked by `tests/test_golden.py`.
4. **One driver-heterogeneity rule.** tau LogNormal clipped to [tau_min, tau_max] (0.5, 3.0), action_interval LogNormal clipped to [0.3, 3.0], slowdown_prob Normal clipped to [0, 1], drawn in that order from their own streams, only when the spread is above 0: `odca.entity.driver.TraitSampler`, the only copy. Checked by `tests/test_driver_traits.py` and the golden.
5. **Units stay inside.** Cells, cells/s and seconds everywhere in `odca/`; km/h, veh/h and veh/km appear only at the reporting edge, through `CELL_LENGTH_M`.
6. **Driver and vehicle keep to the link contract** (D-2026-09-19-24, -30). The driver reads its vehicle's state and neighbours through cells, and changes the vehicle only through `set_target_speed` and `request_direction` (a lane change carries its reason, D-2026-10-03-1); the vehicle calls its driver to wake it (`wake`), to pick the speed again where the limit changes (`evaluate_speed`, D-2026-09-20-4), to judge a gap or a blockage (`accepts_gap`, `sees_blockage`, `evaluate_direction` when stopped), and reads its tau, action interval, lane-change patience and merge priority. Checked by review; a driver writing a vehicle field is a finding.
7. **A new capability is off by default,** and every paper's golden matches with it off. Checked by `tests/test_golden.py`.

## Proof strategy
How a change is shown to be neutral, and how a change that is meant to move a number is shown
to move only that number.

- **Goldens.** `uv run pytest`: every paper's fingerprint (quick mode; paper_odca_des seeds 1-3, paper_lc_logistic seed 42, D-2026-10-03-2, with one MOBIL and one Gipps run, D-2026-10-03-3; stats and counters) matches exactly. During the code-quality refactor a golden may change: re-record it and state which values moved and why (Kerem, 2026-09-19).
- **A change that moves a paper's numbers** gets its own `D-` id here and is noted in that paper's STATUS, whose quoted numbers are rechecked there.
- Only quick goldens run per change; full paper reruns belong to the papers.

## Longer material
What does not fit in two pages lives under `docs/` and is linked from the row or section it
supports; a doc no row links is a candidate for deletion.

`docs/code-review-2026-09-19.md`: the Opus principal-engineer review; its neutral items shipped in PR #9, the rest are BACKLOG B7 to B9.
`docs/config-and-driver-design.md`: the ConfigMixin pattern and the Driver split, with examples (D-2026-09-19-23, -24).
`docs/cell-overlap.md`: two vehicles in one cell at crawl speed, the release rules measured (D-2026-10-02-4, replaced by D-2026-10-02-6).
`docs/lane-change-rate.md`: lane-change probability per distance and per second (D-2026-09-19-22).

## Change protocol
A structural change (a new module, a moved boundary, a changed contract or type) starts with
`/architect`, cites a `D-` id from `DECISIONS.md` in its commit, and is reviewed by `/reviewer`
against this file. A behavior change cites the decision that moved the number and updates every
place the number is quoted in the same PR.
