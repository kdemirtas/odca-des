# HANDOVER: odca-des
Type: generic
Resume point. Full detail in `STATUS.md` (top blockquote); shape of the code in `ARCHITECTURE.md`.

## CURRENT: refactor N2 to N8 shipped (2026-09-19)
- Decisions to D-2026-09-19-35; golden re-recorded for D-2026-09-19-31 (every run moved, STATUS N4b), unchanged by N5 to N8.
- Open: assumptions A-1 to A-7, A-9 to A-17, A-19; the discretionary lane-change question (`docs/lane-change-rate.md`, paper-odca-des AGENDA).
**RESUME:** no ranked item left here; paper-odca-des N9 to N11 drive what comes next. BACKLOG B7 to B9 hold the review's non-neutral speed and memory items.

## NEXT STEPS (pick up here)
None ranked. A capability a paper needs is added here, off by default, with its golden (D-2026-09-19-6).

## Infra
- Repo: `kdemirtas/odca-des` (kdemirtas, private until publication with paper-odca-des); push with `GH_TOKEN=$(gh auth token --user kdemirtas)`.
- Python: `uv`, `.venv/`; `uv run pytest`.
- Users: `~/Papers/paper-odca-des` (switched), `paper-lc-logistic`, `paper-odca-platoon`, `paper-odca-adaptive-platoon` (frozen copies until they switch, paper-odca-des BACKLOG B6).
- License: MIT (paper-odca-des D-2026-09-19-10).
