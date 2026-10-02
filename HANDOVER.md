# HANDOVER: odca-des
Type: generic
Resume point. Full detail in `STATUS.md` (top blockquote); shape of the code in `ARCHITECTURE.md`.

## CURRENT: a cell is not released under its vehicle; the golden moved (2026-10-02)
- Decisions to D-2026-10-02-4. The last is a model fix found by the test for invariant 1: a
  crawling vehicle used to be joined in its cell by the one behind (2,896 of 7,415,365 passages
  in the golden runs). Now the lock waits until the vehicle has left when crossing takes longer
  than tau. Evidence and the rejected alternative in `docs/cell-overlap.md`.
- Golden re-recorded, 348 of 504 values moved. `uv run pytest`: 99 passed, 3 skipped (viewer).
- Also shipped: the strict per-seed JSON reader (D-2026-10-02-3) and the rear gap scan on
  `look_behind` (D-2026-10-02-2). Both invariants now have tests (`tests/test_invariants.py`).
- Earlier the same day, PR #24: `ARCHITECTURE.md` retrofitted to the code; the flag
  `dlc_requires_advantage` goes at the last paper's switch-over (D-2026-10-02-1, BACKLOG B13).
**RESUME:** paper-odca-des must rerun its 124 jobs under D-2026-10-02-4 before it quotes any
number, and its STATUS does not say so yet. Here, `/next-task` takes NEXT 1.

## NEXT STEPS (pick up here)
Ranked by `/architect` retrofit on 2026-10-02. Each is behaviour-neutral and closes on
`uv run pytest` with the golden matching exactly.
1. `SimulationResult.config_yaml` goes through `odca.params`, so `simulation/` stops importing
   omegaconf and the YAML conversion has one copy.
2. `edie_fd_points` takes 7 parameters (the limit is 6): pass the region and the measurement
   window as one type. Changes a signature paper-odca-des calls, so `/architect` names the type
   first.
3. Vehicle ids counted per run (in `VehicleFactory`) instead of the class-level
   `Vehicle._id_counter` that `Simulation.__init__` resets: two simulations built before either
   runs share one counter today. Ids label vehicles only, so no number moves.
4. Text only: the docstring of `odca/entity/vehicle.py` still says the vehicle makes its driver
   "react now" (gone since D-2026-09-20-4); `tests/golden/paper_odca_des/configs/simulation.yaml`
   (line 9) writes a paper-odca-des decision id with a space instead of the colon.

A capability a paper needs is added here, off by default, with its golden
(paper-odca-des:D-2026-09-19-6).

## Infra
- Repo: `kdemirtas/odca-des` (kdemirtas, public since 2026-09-22); push with `GH_TOKEN=$(gh auth token --user kdemirtas)`.
- Python: `uv`, `.venv/`; `uv run pytest`.
- Users: `~/Papers/paper-odca-des` (switched), `paper-lc-logistic`, `paper-odca-platoon`, `paper-odca-adaptive-platoon` (frozen copies until they switch, paper-odca-des BACKLOG B6).
- License: MIT (paper-odca-des:D-2026-09-19-10).
