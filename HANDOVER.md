# HANDOVER: odca-des
Type: generic
Resume point. Full detail in `STATUS.md` (top blockquote); shape of the code in `ARCHITECTURE.md`.

## CURRENT: assumptions being walked with Kerem (2026-09-20)
- Decisions to D-2026-09-20-5. Golden re-recorded 2026-09-20 for the three new stats keys
  (`avg_cells_held`, `avg_origin_wait`, `num_never_entered`): no value moved, 24 runs, 86 tests.
- Closed today: A-1 (t=0 destinations), A-2 (travel time starts at the origin cell), A-3 corrected
  (free-flow speed per vehicle and per cell), A-4 corrected (occupancy reported beside density).
  Also fixed: a speed limit now takes effect on the cell that posts it (D-2026-09-20-4, closing
  BACKLOG B11 the day it opened). BACKLOG B10 closed by D-2026-09-20-5.
- Open: 13 assumption rows, A-2026-09-19-9 next, the discretionary lane-change rate among them
  (`docs/lane-change-rate.md`, paper-odca-des AGENDA). BACKLOG B7 to B9 hold the review's
  non-neutral speed and memory items.
**RESUME:** `/next-assumption` here takes A-2026-09-19-9 (readable origin and destination names in
the configs instead of the dissertation's letters). Nothing in the manuscript can quote the new
occupancy and origin-wait numbers until paper-odca-des reruns its 124 jobs.

## NEXT STEPS (pick up here)
None ranked. A capability a paper needs is added here, off by default, with its golden (D-2026-09-19-6).

## Infra
- Repo: `kdemirtas/odca-des` (kdemirtas, private until publication with paper-odca-des); push with `GH_TOKEN=$(gh auth token --user kdemirtas)`.
- Python: `uv`, `.venv/`; `uv run pytest`.
- Users: `~/Papers/paper-odca-des` (switched), `paper-lc-logistic`, `paper-odca-platoon`, `paper-odca-adaptive-platoon` (frozen copies until they switch, paper-odca-des BACKLOG B6).
- License: MIT (paper-odca-des D-2026-09-19-10).
