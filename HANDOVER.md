# HANDOVER: odca-des
Type: generic
Resume point. Full detail in `STATUS.md` (top blockquote); shape of the code in `ARCHITECTURE.md`.

## CURRENT: paper-lc-logistic is switching over (2026-10-03)
- Lane changes are logged with their reason (D-2026-10-03-1, A-2026-10-03-1 open) and
  paper-lc-logistic has its golden (D-2026-10-03-2). Still to come from that paper: driver-class
  selection for its MOBIL and Gipps drivers, and the rate-rule options.
- Every item `/architect` ranked on 2026-10-02 is shipped (PR #25 to #27). The last two: vehicle
  ids are counted per run by `VehicleFactory`, a hand-built vehicle has id `None`, and two stale
  lines of text are corrected.
- Decisions to D-2026-10-02-5. The one that moved numbers: a cell is not released while its
  vehicle is still in it (D-2026-10-02-4, `docs/cell-overlap.md`), golden re-recorded, 348 of
  504 values moved. The rest are neutral: strict per-seed JSON reader (-3), rear gap scan on
  `look_behind` (-2), one YAML conversion in `odca.params`, `edie_fd_points` on a
  `SpaceTimeRegion` (-5).
- `ARCHITECTURE.md` carries no `drift:` mark on a Boundaries or Data contracts row.
  `dlc_requires_advantage` goes at the last paper's switch-over (D-2026-10-02-1, BACKLOG B13).
- The tag `v0.1.0` is at `66b6a72`, before `dlc_requires_advantage` existed, so it cannot run
  paper-odca-des; that paper's numbers came from `9a3897b`. Kerem's call, with the paper's
  decision on the release rule (paper-odca-des AGENDA, Open decisions).
**RESUME:** nothing ranked here. paper-odca-des decides first: submit on the old release rule,
or rerun its 124 jobs under D-2026-10-02-4. Then BACKLOG: B15 (saturation flow), B12, B7 to B9.

## NEXT STEPS (pick up here)
None ranked. A capability a paper needs is added here, off by default, with its golden
(paper-odca-des:D-2026-09-19-6).

## Infra
- Repo: `kdemirtas/odca-des` (kdemirtas, public since 2026-09-22); push with `GH_TOKEN=$(gh auth token --user kdemirtas)`.
- Python: `uv`, `.venv/`; `uv run pytest`.
- Users: `~/Papers/paper-odca-des` (switched), `paper-lc-logistic` (logistic runs switched 2026-10-03), `paper-odca-platoon`, `paper-odca-adaptive-platoon` (frozen copies until they switch, paper-odca-des BACKLOG B6).
- License: MIT (paper-odca-des:D-2026-09-19-10).
