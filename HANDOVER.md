# HANDOVER: odca-des
Type: generic
Resume point. Full detail in `STATUS.md` (top blockquote); shape of the code in `ARCHITECTURE.md`.

## CURRENT: assumptions being walked with Kerem (2026-09-20)
- Decisions to D-2026-09-20-12. Golden re-recorded twice on 2026-09-20, for the three new stats
  keys (`avg_cells_held`, `avg_origin_wait`, `num_never_entered`) and for the counter split: no
  value moved either time, 24 runs, 86 tests.
- Closed today: A-1 (t=0 destinations), A-2 (travel time starts at the origin cell), A-3 corrected
  (free-flow speed per vehicle and per cell), A-4 corrected (occupancy reported beside density),
  A-9 (readable origin and destination names, D-2026-09-20-6), A-10 (the any-lane `end` kept for
  the lane-drop runs, D-2026-09-20-7), A-11 (the wrong end lane counted as a missed exit,
  D-2026-09-20-8), A-6 (the exposure references, D-2026-09-20-9, written into the manuscript),
  A-7 (exposure starts at the first evaluation, the cooldown does not bank it, D-2026-09-20-10),
  A-12 (the vehicle constants as config fields, D-2026-09-20-11), A-13 (the vehicle-driver link and
  the counter split, D-2026-09-20-12).
- `lc_failures` is now two stored counters, `lc_patience_failures` and `gap_rejections`
  (D-2026-09-20-12, Kerem's call). Golden re-recorded: 24 runs, nothing moved, the two sum to the
  old key. Patience failures are 0 everywhere and every failure is a refused gap: BACKLOG B12.
- Also fixed: a speed limit now takes effect on the cell that posts it (D-2026-09-20-4, closing
  BACKLOG B11 the day it opened). BACKLOG B10 closed by D-2026-09-20-5.
- Open: 6 assumption rows, A-2026-09-19-14 next, the discretionary lane-change rate among them
  (`docs/lane-change-rate.md`, paper-odca-des AGENDA). BACKLOG B7 to B9 hold the review's
  non-neutral speed and memory items.
**RESUME:** `/next-assumption` here takes A-2026-09-19-14 (`AutonomousController` and
`AutonomousDriver` as the names, one `VehicleFactory`, vehicle kinds told apart by `kind`). Nothing
in the manuscript can quote the new
occupancy and origin-wait numbers until paper-odca-des reruns its 124 jobs.

## NEXT STEPS (pick up here)
None ranked. A capability a paper needs is added here, off by default, with its golden
(paper-odca-des D-2026-09-19-6).

## Infra
- Repo: `kdemirtas/odca-des` (kdemirtas, private until publication with paper-odca-des); push with `GH_TOKEN=$(gh auth token --user kdemirtas)`.
- Python: `uv`, `.venv/`; `uv run pytest`.
- Users: `~/Papers/paper-odca-des` (switched), `paper-lc-logistic`, `paper-odca-platoon`, `paper-odca-adaptive-platoon` (frozen copies until they switch, paper-odca-des BACKLOG B6).
- License: MIT (paper-odca-des D-2026-09-19-10).
