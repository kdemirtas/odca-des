# HANDOVER: odca-des
Type: generic
Resume point. Full detail in `STATUS.md` (top blockquote); shape of the code in `ARCHITECTURE.md`.

## CURRENT: two retrofit items closed, the model fix of PR #25 stands (2026-10-02)
- Decisions to D-2026-10-02-5. The last: `edie_fd_points` takes one `SpaceTimeRegion` in place
  of five values; paper-odca-des's three callers are edited in that repo in the same pass.
- The YAML conversion has one copy, `odca.params.to_yaml`; `simulation/` no longer imports
  omegaconf. `ARCHITECTURE.md` carries no `drift:` mark on a Boundaries or Data contracts row.
- Before these, PR #25: a cell is not released while its vehicle is still in it
  (D-2026-10-02-4, `docs/cell-overlap.md`), golden re-recorded, 348 of 504 values moved; the
  strict per-seed JSON reader (-3) and the rear gap scan on `look_behind` (-2).
- PR #24: `ARCHITECTURE.md` retrofitted to the code; `dlc_requires_advantage` goes at the last
  paper's switch-over (D-2026-10-02-1, BACKLOG B13).
**RESUME:** paper-odca-des must rerun its 124 jobs under D-2026-10-02-4 before it quotes any
number. Here, `/next-task` takes NEXT 1.

## NEXT STEPS (pick up here)
Ranked by `/architect` retrofit on 2026-10-02. Each is behaviour-neutral and closes on
`uv run pytest` with the golden matching exactly.
1. Vehicle ids counted per run (in `VehicleFactory`) instead of the class-level
   `Vehicle._id_counter` that `Simulation.__init__` resets: two simulations built before either
   runs share one counter today. Ids label vehicles only, so no number moves.
2. Text only: the docstring of `odca/entity/vehicle.py` still says the vehicle makes its driver
   "react now" (gone since D-2026-09-20-4); `tests/golden/paper_odca_des/configs/simulation.yaml`
   (line 9) writes a paper-odca-des decision id with a space instead of the colon.

A capability a paper needs is added here, off by default, with its golden
(paper-odca-des:D-2026-09-19-6).

## Infra
- Repo: `kdemirtas/odca-des` (kdemirtas, public since 2026-09-22); push with `GH_TOKEN=$(gh auth token --user kdemirtas)`.
- Python: `uv`, `.venv/`; `uv run pytest`.
- Users: `~/Papers/paper-odca-des` (switched), `paper-lc-logistic`, `paper-odca-platoon`, `paper-odca-adaptive-platoon` (frozen copies until they switch, paper-odca-des BACKLOG B6).
- License: MIT (paper-odca-des:D-2026-09-19-10).
