# HANDOVER: odca-des
Type: generic
Resume point. Full detail in `STATUS.md` (top blockquote); shape of the code in `ARCHITECTURE.md`.

## CURRENT: the contract is retrofitted to the code, seven items ranked (2026-10-02)
- `/architect` retrofit on 2026-10-02 read the code against `ARCHITECTURE.md`. All ten module
  boundaries match their imports. Three rows are marked `drift:` there: the per-seed JSON reader
  fills a missing key, `accepts_gap` scans backward with `look_ahead`, and
  `simulation/result.py` imports omegaconf itself.
- Decisions to D-2026-10-02-3: the flag `dlc_requires_advantage` is deleted at the last paper's
  switch-over (-1, BACKLOG B13), the rear gap scan reads `look_behind` (-2), the per-seed JSON
  reader is strict (-3). D-2026-09-22-1 got the body it lacked.
- Docs only, no code changed. `uv run pytest` on main: 90 passed, 24 golden runs matching.
- Before it, 2026-09-22: `dlc_requires_advantage` added off by default (D-2026-09-22-1), the
  golden re-recorded twice, for `num_never_entered` over every vehicle (-2) and for the flag
  on, as the paper runs it (-3).
**RESUME:** `/next-task` takes NEXT 1, the strict per-seed JSON reader (D-2026-10-02-3).
`STATUS.md` TL;DR and Current numbers, and `PROJECT.md`, still describe 2026-09-20: `/fix-drift`.

## NEXT STEPS (pick up here)
Ranked by `/architect` retrofit on 2026-10-02, by what would ship wrong first. Each is
behaviour-neutral and closes on `uv run pytest` with the golden matching exactly.
1. Make the per-seed JSON reader strict (D-2026-10-02-3): `RunRecord.from_json` requires all
   seven keys and names the file and the key it misses; a test in `tests/test_experiment.py`
   for a file without `hdv_action_interval`. Then read paper-odca-des's 180 files through it.
2. Scan for the follower with `look_behind` in `Driver.accepts_gap` (D-2026-10-02-2). The two
   ranges are equal in both YAMLs, so the golden must not move; a unit test with unequal ranges.
3. Assert the two invariants that have no test: one vehicle per cell at every trajectory stamp,
   and single-lane capacity 3600 / (tau + d / v_max) = 2127 veh/h at the human defaults with no
   spread. Tests only.
4. `SimulationResult.config_yaml` goes through `odca.params`, so `simulation/` stops importing
   omegaconf and the YAML conversion has one copy.
5. `edie_fd_points` takes 7 parameters (the limit is 6): pass the region and the measurement
   window as one type. Changes a signature paper-odca-des calls, so `/architect` names the type
   first.
6. Vehicle ids counted per run (in `VehicleFactory`) instead of the class-level
   `Vehicle._id_counter` that `Simulation.__init__` resets: two simulations built before either
   runs share one counter today. Ids label vehicles only, so no number moves.
7. Text only: `odca/entity/vehicle.py` (line 10) still says the vehicle makes its driver "react now"
   (gone since D-2026-09-20-4); `tests/golden/paper_odca_des/configs/simulation.yaml` (line 9) writes
   a paper-odca-des decision id with a space instead of the colon.

A capability a paper needs is added here, off by default, with its golden
(paper-odca-des:D-2026-09-19-6).

## Infra
- Repo: `kdemirtas/odca-des` (kdemirtas, public since 2026-09-22); push with `GH_TOKEN=$(gh auth token --user kdemirtas)`.
- Python: `uv`, `.venv/`; `uv run pytest`.
- Users: `~/Papers/paper-odca-des` (switched), `paper-lc-logistic`, `paper-odca-platoon`, `paper-odca-adaptive-platoon` (frozen copies until they switch, paper-odca-des BACKLOG B6).
- License: MIT (paper-odca-des:D-2026-09-19-10).
