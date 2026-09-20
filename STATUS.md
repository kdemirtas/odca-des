# odca-des: status
> Read `PROJECT.md` first (the spec). This file = where things stand and what to do next. Entries
> older than the current wave are in `STATUS_ARCHIVE.md`. Last updated **2026-09-19**.
> **Current wave:** extraction and refactor, since 2026-09-19

## TL;DR
Shared ODCA simulator, extracted from paper-odca-des 2026-09-19. Bugs fixed, lane-change rate
rule in, refactor N2 to N8 shipped 2026-09-19; next is whatever paper-odca-des N11 needs, and BACKLOG.

## Current numbers
Goldens: paper_odca_des 24 quick runs (S1-S4 and bottleneck, seeds 1-3), re-recorded 2026-09-19
after one lane-change request makes one lane change (D-2026-09-19-31); unchanged by N5 to N8 and by D-2026-09-20-3; `uv run pytest` 85/85 passed.


## 2026-09-20: free flow is per vehicle and per cell
- `v_f(n, c) = min(v_max(n), v_lim(c))` replaces `v_max(n)` as the reference in `delay`; every
  trajectory record carries it as `v_free` (D-2026-09-20-3, Kerem corrected A-2026-09-19-3). A cell
  driven at a posted limit no longer counts as delay; a work zone changes the free-flow trip time
  instead. The manuscript's Eq. free_flow_speed and Eq. delay say the same.
- No number moved: every cell in every scenario of paper-odca-des posts 5.2 cells/s and both vehicle
  types have `v_max` 5.2. Golden 24/24 exact, 85 tests pass (`tests/test_delay.py` new).
- Found on the way: a limit change takes effect one cell late at both ends of a zone, 0.577 s each
  way at a 1.3 cells/s work zone. BACKLOG B11; no scenario here has a varying limit.

## 2026-09-19 (N8): neutral speed-ups from the code review
- Cell neighbour links and occupant as plain slots set at build time, `Lane.make_periodic`, per-lane closed-cell count, exited AVs pruned from the controller, dead code removed (D-2026-09-19-35, assumption A-19). Non-neutral review items parked as BACKLOG B7 to B9; the review's correctness items were fixed earlier (D-2026-09-19-11 to -20).
- Proof: golden 24/24 exact; paper ring-road FD points byte-identical against main; `tests/test_infrastructure.py`; 83 tests. Wall time (300 s quick, best of 3): S1 7.40 to 7.17 s, S3 10.34 to 8.90 s. Review: conformance 1 (`Cell` type hint imported `entity`, removed), correctness 0.
- The paper's `diagnose_fd_capacity.py` must use `lane.make_periodic()` with this change (paper N10).

## 2026-09-19 (N7): viewers in the package
- `odca.viewer` (snapshots, matplotlib animation and time-space diagram, pygame playback), each from a `SimulationResult` (D-2026-09-19-34, assumption A-17). The paper's `visualize.py` and `animate.py` are thin CLIs.
- Proof: headless render of all three from an S1 run; `tests/test_viewer.py`; 80 tests. Review: conformance 0; correctness 2 (time window checked one end only, no pygame test), fixed.

## 2026-09-19 (N6): experiment kit
- `odca.experiment` (run records, strict per-seed JSON, aggregation) and `odca.analysis.mean_ci95` (D-2026-09-19-33, assumption A-16). The paper's two runners and `aggregate_multiseed.py` use it; their three t-table copies are gone.
- Proof: the five aggregate CSVs rebuilt from 69 existing per-seed JSONs are byte-identical; rewired runners reproduce golden stats and counters; `run_once` tested; 76 tests. Review: correctness 2 (untested `run_once`, undocumented run-only wall time), conformance 1 (runner default folder, fixed in the paper); all addressed.

## 2026-09-19 (N5): typed run result
- `Simulation.run()` returns `SimulationResult` (config, vehicles, generated count, `RunCounters`), `odca/simulation/result.py` (D-2026-09-19-32, assumption A-15). Golden exact; 68 tests; paper runners moved to attributes in the same pass.

## 2026-09-19 (N4b): one lane-change request, one lane change
- `Vehicle._advance_to` uses up the request after a lateral move (D-2026-09-19-31); test `test_one_request_makes_one_lane_change` (2 changes from one request before).
- Golden re-recorded, every run moved. Lane changes per km, delay (s), throughput (veh/h), missed exits, before to after:

| run | lc/km | delay | throughput | missed |
|---|---|---|---|---|
| S1 seed 1 | 4.98 to 1.81 | 30.6 to 22.8 | 2880 to 3080 | 57 to 38 |
| S1 seed 2 | 4.77 to 1.89 | 26.8 to 24.2 | 2867 to 3067 | 45 to 30 |
| S2 seed 1 | 4.10 to 1.40 | 26.4 to 18.1 | 3147 to 3387 | 36 to 25 |
| S3 seed 1 | 3.18 to 1.09 | 19.3 to 11.9 | 3547 to 3667 | 35 to 14 |
| S4 seed 1 | 2.09 to 0.65 | 9.4 to 6.3 | 3787 to 4027 | 27 to 13 |
| BN 0% AV seed 1 | 1.07 to 0.94 | 80.7 to 84.4 | 2460 to 2393 | 0 to 0 |
| BN 70% AV seed 1 | 0.42 to 0.34 | 4.8 to 6.1 | 3547 to 3540 | 0 to 0 |

- Not all one way: with no AVs the bottleneck delay rises on seeds 1 and 3 (80.7 to 84.4 s, 67.5 to 69.9 s) and falls on seed 2 (69.1 to 66.7 s); a vehicle leaving the closed lane now needs one decision per lane change. Review (correctness): also noted that a DLC can take the next decision of a vehicle still short of its exit lane, part of the open DLC question below.
- ⏳ S1 still makes about 2.3 lane changes per vehicle-km, 45% away from the needed lane, from the zero-advantage DLC rate; two candidate rules measured in `docs/lane-change-rate.md`, Kerem decides.

## 2026-09-19 (N4): driver split from the vehicle
- `Vehicle(env, cfg, driver, origin_cell, destination)` keeps the physical side; `Driver`, `HumanDriver` (own process), `AutonomousDriver` (registers with `AutonomousController`, renamed from `AVController`) hold the decisions; `VehicleFactory` builds every vehicle; `HDV`, `AV`, `VehicleType`, `config_kwargs` gone; the seven class constants are config fields with the same defaults (D-2026-09-19-30, assumptions A-12 to A-14 made unattended).
- Proof: golden 24/24 exact; paper demand sweep, ring-road FD and car-following scripts byte-identical old against new; 66 tests. Review: correctness 0 findings, conformance 2 em-dashes (fixed).
- `validate` now accepts whole numbers in float tables (a demand of `400` was refused).
- ⏳ Found while plotting the demo: a lane-change request persists after the change, so one decision makes several lane changes in a row (S1: 3.9 lane changes per vehicle-km, half away from the needed lane). Fixed next as its own PR (golden moves). The zero-advantage DLC rate (0.047/s) is the rest of the excess; left to Kerem (AGENDA-style open question in `docs/lane-change-rate.md`).

## 2026-09-19 (night): N3 one trait sampler
- `odca/entity/driver.py`: `DriverTraits` and `TraitSampler`, the only copy of the driver
  heterogeneity rule (was in generator, engine and two paper scripts); clip ranges are now
  `HumanDriverConfig` fields. Proof: golden exact, 63/63; the paper's old copy and the sampler give
  2000 identical draws on the same seeds.

## 2026-09-19 (later): N2 configs, YAML, named places, OD demand, endpoint cells, incidents
- **N2 done** (D-2026-09-19-23): `odca/params.py` holds every config schema (frozen, slotted
  dataclasses) and `ConfigMixin`; `validate` checks types, unknown keys and missing values and
  builds bottom-up; nothing in `odca` imports a paper's `config`. Lane-change configs are a
  family picked by `model:` (Kerem's `BaseLaneChangeConfig` / `LogisticLaneChangeConfig`).
- **YAML** (D-2026-09-19-25): package defaults in `odca/configs/`, scenarios in the paper;
  file references, `odca://`, `_base_` overrides at any depth.
- **Demand and places** (D-2026-09-19-26, dissertation 4.1): the network declares named origins
  and destinations (one end per lane); demand is veh/h per named pair, one generator per pair.
  S1 spreads end traffic over the four lane ends. Every golden run moved (seed 1 S1: lane
  changes per km 2.09 -> 4.98, delay 29.1 -> 30.6 s, throughput 3130 -> 2880 veh/h).
- **Endpoint cells** (D-2026-09-19-27): `OriginCell`, `DestinationCell`; transparent unless
  limited (golden exact), then capped at 3600 / (tau + 1/v) veh/h per lane.
- **Incidents** (D-2026-09-19-28): `IncidentConfig` in `SimConfig.incidents`; overlapping
  incidents stack and every cell returns to its own state.
- **Review**: correctness found a missed off-ramp keeping the old lane, overlapping incidents
  corrupting each other, a speed limit of 0 crashing, and a test that proved nothing; all fixed
  with tests. Conformance: HDV/AV inits at 9 parameters, left to N4 (they are removed there).
- Proof: `uv run pytest` 59/59, golden 24/24; gate WARN (long inits, N4).
- A-2026-09-19-8 accepted -> D-2026-09-19-29. Open: A-1 to A-7, A-9 to A-11.

## 2026-09-19: extraction, bug fixes, lane-change rate, refactor design
- **Created** from paper-odca-des `code/odca/` with its history (git filter-repo); paper-odca-des
  depends on it editable. First move byte-identical: golden 24/24 exact from both sides.
- **Bug fixes** (Kerem: fix every bug, paper is the spec), each a decision: exit lane any lane at
  the segment end (D-2026-09-19-11); one position-change point `_on_cell_change` at arrival, lock unchanged
  (D-2026-09-19-12); lane-change safety rejects occupied or locked cells (D-2026-09-19-13); summary window by exit time
  (D-2026-09-19-14); per-cell delay (D-2026-09-19-15); one exit path, missed off-ramps retargeted and counted, lateral
  race fixed (D-2026-09-19-17); lane changes counted on grant, cooldown for DLC only (D-2026-09-19-18); AVs act at the
  controller rate, initial vehicles follow the AV share (D-2026-09-19-19); measurement fixes, SimPy event
  count, all speed evaluations, lane changes per km over distance driven, space-mean speed (D-2026-09-19-20).
  Golden re-recorded after each; every run moved. S1 seed 1 now reports about 2.25M SimPy events
  (the old counter summed about 57k), so the paper's event and scalability claims need restating.
- **Lane-change rate** (D-2026-09-19-22, Kerem chose "MLC per distance, DLC per second"): q = 1-(1-p)^x, x =
  cells driven / 5.2 (MLC) or seconds (DLC); `odca/models/lane_changing/rate.py`. Where half the
  vehicles have attempted the MLC: 0.60 in every case (was 0.85 for AVs, 0.60 free-flow HDVs).
  Golden, seed 1 old -> new: S1 lane changes 231 -> 235, delay 30.8 -> 29.1 s; S4 delay 9.08 ->
  10.4 s; bottleneck 0% AV delay 69 -> 74.5 s. Write-up `docs/lane-change-rate.md`, including the
  finding that DLC fires at p = 0.047/s with no speed advantage (for paper-lc-logistic).
- **Refactor design** (`/architect`): one config per class with `ConfigMixin`, schemas in
  `odca/params.py`, omegaconf only at the run boundary (D-2026-09-19-23; a DictConfig read measured about 250
  times slower than a dataclass slot); Driver split from Vehicle with the two-way link contract
  Kerem agreed (D-2026-09-19-24). `docs/config-and-driver-design.md`. BACKLOG B5 (segment controllers, a model
  feature), B6 (own event loop instead of SimPy, v2).
- Assumptions open: 14 rows in `ASSUMPTIONS.md`; A-2026-09-19-1 closed 2026-09-20 as D-2026-09-20-1,
  A-2026-09-19-2 as D-2026-09-20-2 (origin wait reported separately once a rerun can carry it, BACKLOG B10),
  A-2026-09-19-3 corrected as D-2026-09-20-3 (free flow per vehicle and per cell).
- ⏳ Gate WARN: `params` (long inits), closed by N4.

## How to run
`uv run pytest` (add `-n 12` for parallel; `--write-golden` re-records, only under a decision)
