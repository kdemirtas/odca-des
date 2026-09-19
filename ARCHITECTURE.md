# ARCHITECTURE: odca-des
> **Owned by `/architect`. Two pages max. Last updated 2026-09-19.** Code follows this file; when
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
| `odca/params.py` | `ConfigMixin`; every config schema (`VehicleConfig`, `HumanDriverConfig`, `AutonomousDriverConfig`, `ControllerConfig`, `NetworkConfig`, `ODFlow`, `SimConfig`); `CELL_LENGTH_M` (D-2026-09-19-23) | stdlib, omegaconf | any other `odca` module, any paper |
| `odca/rng.py` | `RNGRegistry`: one `SeedSequence` stream per source | numpy | any other `odca` module |
| `odca/models/` | Newell, MLC and DLC probabilities; pure functions | stdlib | simpy, any `odca` module |
| `odca/infrastructure/` | `Cell`, `Lane`, `Freeway` | simpy | entity, simulation |
| `odca/entity/` | `Vehicle` (physical: cell label, lock, movement, trajectory), `Driver`, `HumanDriver`, `AutonomousDriver`, `AutonomousController`, `DriverTraits` and their sampler, `TrajectoryRecord` (D-2026-09-19-24) | infrastructure, models, params | simulation, analysis, experiment |
| `odca/simulation/` | `Simulation`, `VehicleGenerator`, `SimulationResult`, RNG stream order | entity, infrastructure, rng, params | analysis, experiment, viewer |
| `odca/analysis/` | Edie FD, passage-time flow, `summary_statistics`, `mean_ci95` (the only interval code) | entity (read-only), params | simulation, experiment |
| `odca/baselines/` | NaSch | numpy | the rest of `odca` |
| `odca/experiment/` | run a scenario over a seed list, per-seed JSON writer, aggregation into the CSV schema below | simulation, analysis, params | viewer, any paper |
| `odca/viewer/` | pygame playback, matplotlib animation; extra `[viewer]` | simulation, entity, params | experiment |
| `tests/` | unit tests; `tests/golden/<paper>/` scenario definitions and `fingerprint.json` per paper | everything in `odca` | a paper repo (fixtures are copied in, not imported) |

Papers keep: parameter values (`config.py`), scenario definitions, figure scripts, diagnostics. They import `odca`; nothing in `odca` imports a paper. drift: `odca/params.py`, `odca/experiment/`, `odca/viewer/` do not exist yet, and the core still imports the paper's `config` (N2, N6, N7); `Driver` is still inside `Vehicle`, with `HDV`/`AV` subclasses and the `vtype`/`dlc_enabled` switches (N4).

## Layout

    odca/            the package (import name odca)
    tests/           unit tests; tests/golden/<paper>/ = config.py, scenarios.py, fingerprint.json per paper
    docs/            longer reference docs ARCHITECTURE.md links
    pyproject.toml   distribution odca-des, extra [viewer], dev group pytest

## Data contracts
Every artifact that crosses a module boundary or leaves the project: its grain, its writer, its
readers, and where the contract is asserted. "Nowhere" is a legal entry and a backlog item.

| Artifact | Grain (key) | Written by | Read by | Asserted in |
|---|---|---|---|---|
| per-seed JSON | (scenario, seed, hdv_action_interval) | `odca.experiment` | `odca.experiment` aggregation | a schema test (planned) |
| aggregate CSV | (scenario, av_penetration, hdv_action_interval, metric): n, mean, std, ci95_lo, ci95_hi | `odca.experiment` | paper figure scripts, manuscript tables | a schema test (planned) |
| `tests/golden/<paper>/fingerprint.json` | (scenario, seed) in quick mode: stats and counters | `golden --write`, only under a decision | the golden test | the golden test, exact match |

## Core types
The concepts the code passes around. Each has one definition; functions take the type, not its
fields.

| Type | Meaning | Defined in |
|---|---|---|
| `VehicleConfig`, `HumanDriverConfig`, `AutonomousDriverConfig`, `ControllerConfig` | one class's parameters each, population values (means and spreads for humans); validated by omegaconf once per run, frozen dataclasses after | `odca/params.py`. drift: today one `VehicleParams` in the paper's `config.py`, unpacked into a 24-parameter `Vehicle.__init__` |
| `DriverTraits` | one driver's sampled values (tau, action interval, slowdown probability), drawn once at creation | `odca/entity/driver.py` (planned, N3) |
| `SimConfig`, `NetworkConfig`, `ODFlow` | one run: geometry, demand, AV penetration, seed, duration, warm-up, numerics (traversal sub-step) | `odca/params.py` (today `config.py`) |
| `Cell`, `Lane`, `Freeway` | the spatial resources | `odca/infrastructure/` |
| `Vehicle` | one vehicle's physical side: position label, cell lock with delayed release (reads tau from its driver), movement, exit, trajectory | `odca/entity/vehicle.py` |
| `Driver` (`HumanDriver`, `AutonomousDriver`) | the decisions: target speed, direction, lane-change curves, gap acceptance, exposure since the last decision. `HumanDriver` runs its own SimPy process; `AutonomousDriver` is called by an `AutonomousController` | `odca/entity/driver.py` (planned, N4) |
| `TrajectoryRecord` | one T(x, n) passage record | `odca/entity/vehicle.py` |
| `SimulationResult` (planned) | vehicles, completed vehicles, counters and config of one run | `odca/simulation/engine.py`. drift: a plain dict today |

## Invariants
What must hold after every run, each with the check that proves it.

1. **One vehicle per cell.** `Cell.resource` has capacity 1. Checked by construction (`cell.py`), no test.
2. **Headway by delayed release.** A cell is released tau seconds after its vehicle leaves it (`_delayed_release`, `_exit`), so homogeneous single-lane capacity is 3600 / (tau + d / v_max) = 2127 veh/h at HDV defaults. Checked by eye in `diagnose_fd_capacity.py`; no assertion (BACKLOG B2).
3. **Same config and seed, same numbers.** `Simulation` spawns its streams in a fixed order: six behaviour streams, then one per OD flow in `od_flows` order. A new stream goes last, or every number moves. Checked by `tests/test_golden.py`.
4. **One driver-heterogeneity rule.** tau LogNormal clipped to [0.5, 3.0], action_interval LogNormal clipped to [0.3, 3.0], slowdown_prob Normal clipped to [0, 1], drawn in that order from their own streams. drift: copied in `generator.py` and `engine.py` here, and in two paper-odca-des scripts (N3).
5. **Units stay inside.** Cells, cells/s and seconds everywhere in `odca/`; km/h, veh/h and veh/km appear only at the reporting edge, through `CELL_LENGTH_M`.
6. **Driver and vehicle keep to the link contract** (D-2026-09-19-24). The driver reads its vehicle's state and neighbours through cells, and changes the vehicle only through its commands (target speed, lane-change request); the vehicle calls its driver only to wake it and to read tau. Checked by review; a driver writing a vehicle field is a finding.
7. **A new capability is off by default,** and every paper's golden matches with it off. Checked by `tests/test_golden.py`.

## Proof strategy
How a change is shown to be neutral, and how a change that is meant to move a number is shown
to move only that number.

- **Goldens.** `uv run pytest`: every paper's fingerprint (quick mode, seeds 1-3, stats and counters) matches exactly. During the code-quality refactor a golden may change: re-record it and state which values moved and why (Kerem, 2026-09-19).
- **A change that moves a paper's numbers** gets its own `D-` id here and is noted in that paper's STATUS, whose quoted numbers are rechecked there.
- Only quick goldens run per change; full paper reruns belong to the papers.

## Longer material
What does not fit in two pages lives under `docs/` and is linked from the row or section it
supports; a doc no row links is a candidate for deletion.

`docs/code-review-2026-09-19.md`: the Opus principal-engineer review that feeds N8.
`docs/config-and-driver-design.md`: the ConfigMixin pattern and the Driver split, with examples (D-2026-09-19-23, -24).
`docs/lane-change-rate.md`: lane-change probability per distance and per second (D-2026-09-19-22).

## Change protocol
A structural change (a new module, a moved boundary, a changed contract or type) starts with
`/architect`, cites a `D-` id from `DECISIONS.md` in its commit, and is reviewed by `/reviewer`
against this file. A behavior change cites the decision that moved the number and updates every
place the number is quoted in the same PR.
