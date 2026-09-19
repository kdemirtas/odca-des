# odca-des: status
> Read `PROJECT.md` first (the spec). This file = where things stand and what to do next. Entries
> older than the current wave are in `STATUS_ARCHIVE.md`. Last updated **2026-09-19**.
> **Current wave:** extraction and refactor, since 2026-09-19

## TL;DR
Shared ODCA simulator, extracted from paper-odca-des 2026-09-19. Bugs fixed, lane-change rate
rule in, refactor design settled; next is the refactor N2 to N8 (ranked list in `HANDOVER.md`).

## Current numbers
Goldens: paper_odca_des 24 quick runs (S1-S4 and bottleneck, seeds 1-3), re-recorded 2026-09-19
after the named-places demand (D-2026-09-19-26); unchanged by N3 and N4; `uv run pytest` 66/66 passed.


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
- Assumptions open: A-2026-09-19-1 to -7 (`ASSUMPTIONS.md`).
- ⏳ Gate WARN: `params` (long inits), closed by N4.

## How to run
`uv run pytest` (add `-n 12` for parallel; `--write-golden` re-records, only under a decision)
