# HANDOVER: odca-des
Type: generic
Resume point. Full detail in `STATUS.md` (top blockquote); shape of the code in `ARCHITECTURE.md`.

## CURRENT: every assumption closed, waiting on the paper (2026-09-20)
- Decisions to D-2026-09-20-18. `ASSUMPTIONS.md` is empty: all thirteen rows left from the
  extraction and the refactor were walked with Kerem on 2026-09-20 and accepted, each one a
  decision (STATUS has the list).
- The one change he asked for on top: `lc_failures` is two stored counters now,
  `lc_patience_failures` and `gap_rejections` (D-2026-09-20-12, PR #16). Golden re-recorded twice
  today, for the D-2026-09-20-5 stats keys and for the split: no value moved either time, 24 runs,
  86 tests.
- What the split showed: patience failures are 0 in all 24 golden runs and every failure is a
  refused gap, because `accepts_gap` refuses a taken cell before the request is made. BACKLOG B12.
- The discretionary lane-change rate is not an assumption row and never was: it is a
  paper-odca-des `AGENDA.md` decision, measured here in `docs/lane-change-rate.md`.
**RESUME:** nothing waiting here. The open work is BACKLOG: B7 to B9 (the code review's speed and
memory items) and B12. Nothing in paper-odca-des can quote the occupancy, origin-wait or split
failure numbers until it reruns its 124 jobs.

## NEXT STEPS (pick up here)
None ranked. A capability a paper needs is added here, off by default, with its golden
(paper-odca-des D-2026-09-19-6).

## Infra
- Repo: `kdemirtas/odca-des` (kdemirtas, private until publication with paper-odca-des); push with `GH_TOKEN=$(gh auth token --user kdemirtas)`.
- Python: `uv`, `.venv/`; `uv run pytest`.
- Users: `~/Papers/paper-odca-des` (switched), `paper-lc-logistic`, `paper-odca-platoon`, `paper-odca-adaptive-platoon` (frozen copies until they switch, paper-odca-des BACKLOG B6).
- License: MIT (paper-odca-des D-2026-09-19-10).
