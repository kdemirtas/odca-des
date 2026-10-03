# HANDOVER: odca-des
Type: generic
Resume point. Full detail in `STATUS.md` (top blockquote); shape of the code in `ARCHITECTURE.md`.

## CURRENT: multi-cell vehicles designed, code not started (2026-10-03)
- 0.1.0 is tagged at `23bbe99` (the merge of PR #28) and archived on Zenodo as
  10.5281/zenodo.23117204; paper-odca-des cites it and reran its 124 jobs under D-2026-10-02-6,
  0 failed. `main` has moved past the tag (PR #29 on).
- paper-odca-des and paper-lc-logistic install this package as an editable path dependency, so
  they follow `main`, not a tag. Their goldens in `tests/golden/` are what hold their numbers.
- One `main` (D-2026-10-03-7): a core change is built here behind a default that leaves every
  golden unchanged.
- Designed, not built: a vehicle holds as many cells as its length (D-2026-10-03-8, ideas I1
  and I3). Three calls of mine are open: A-2026-10-03-3 (whole cells), -4 (the rear cell's lock
  opens tau after the front takes its next cell; a vehicle grows in at the origin), -5 (the
  front is the position, every held cell is labelled, metrics stay on the front).
- paper-lc-logistic's logistic runs are on the package (PR #30 to #34: lane-change log, golden,
  driver class from the config, rate rule, two destination rules; A-2026-10-03-1, -2 open).
- Backlog trimmed by Kerem on 2026-10-03: B5 to B9 and B14 dropped. `dlc_requires_advantage`
  goes at the last paper's switch-over (D-2026-10-02-1, B13).
**RESUME:** N1: build multi-cell vehicles (D-2026-10-03-8), every golden unchanged at length 1.
Then BACKLOG: B15 (saturation flow, remeasure first), B12, B1; B3 (PyPI) last. B2, B13 and B16
wait.

## NEXT STEPS (pick up here)
A capability a paper needs is added here, off by default, with its golden
(paper-odca-des:D-2026-09-19-6).

1. **N1: vehicles that hold several cells** {T1, priority M} (D-2026-10-03-8, on `main` per
   D-2026-10-03-7; structural, changes Invariant 1 and the `Vehicle` and `VehicleConfig` rows of
   `ARCHITECTURE.md` in the same PR). `VehicleConfig.length` in cells, default 1. A vehicle holds
   every cell from its front to its rear; the front takes the next cell, the rear cell is given
   up, the body follows the front through a lane change. Spacing and gaps are measured to the
   leader's rear. Open calls of mine: A-2026-10-03-3 to -5. Proof: every golden unchanged at
   length 1; a test where a 3-cell vehicle holds 3 cells and no cell is ever shared; a test of
   the bus lane change of D-2026-10-03-8 cell by cell.

## Infra
- Repo: `kdemirtas/odca-des` (kdemirtas, public since 2026-09-22); push with `GH_TOKEN=$(gh auth token --user kdemirtas)`.
- Python: `uv`, `.venv/`; `uv run pytest`.
- Users: `~/Papers/paper-odca-des` (switched), `paper-lc-logistic` (logistic runs switched 2026-10-03), `paper-odca-platoon`, `paper-odca-adaptive-platoon` (frozen copies until they switch, paper-odca-des BACKLOG B6).
- License: MIT (paper-odca-des:D-2026-09-19-10).
