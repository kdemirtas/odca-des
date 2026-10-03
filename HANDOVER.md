# HANDOVER: odca-des
Type: generic
Resume point. Full detail in `STATUS.md` (top blockquote); shape of the code in `ARCHITECTURE.md`.

## CURRENT: multi-cell vehicles built, off by default (2026-10-03)
- A vehicle holds as many cells as its length: `VehicleConfig.length`, default 1
  (D-2026-10-03-8). The body follows the front through a lane change; no second lane change
  while the body is in two lanes, and the body drives out behind the front at the exit
  (D-2026-10-03-9). Length above 1 is refused with `stops_for_offramp` on (D-2026-10-03-10, B17).
- Every golden is unchanged at length 1. Open calls of mine: A-2026-10-03-3 (whole cells), -4
  (the rear cell's lock opens tau after the front takes its next cell), -5 (the front is the
  position, metrics stay on the front).
- Not tested at length above 1: ring road, lane-change patience failure, lateral escape,
  autonomous drivers, a vehicle reaching its destination before its full length is on the road.
- 0.1.0 is tagged at `23bbe99` and archived on Zenodo as 10.5281/zenodo.23117204; paper-odca-des
  cites it. `main` has moved past the tag (PR #29 on). One `main` (D-2026-10-03-7).
- paper-odca-des and paper-lc-logistic install this package as an editable path dependency, so
  they follow `main`, not a tag. Their goldens in `tests/golden/` are what hold their numbers.
- Backlog trimmed by Kerem on 2026-10-03: B5 to B9 and B14 dropped. `dlc_requires_advantage`
  goes at the last paper's switch-over (D-2026-10-02-1, B13).
**RESUME:** nothing ranked. Kerem closes A-2026-10-03-3 to -5 (`/next-assumption`). BACKLOG:
B15 (saturation flow, remeasure first), B12, B1; B16 (mixed fleet) and B17 are ready to promote;
B3 (PyPI) last. B2 and B13 wait on the platoon papers.

## NEXT STEPS (pick up here)
None ranked. A capability a paper needs is added here, off by default, with its golden
(paper-odca-des:D-2026-09-19-6).

## Infra
- Repo: `kdemirtas/odca-des` (kdemirtas, public since 2026-09-22); push with `GH_TOKEN=$(gh auth token --user kdemirtas)`.
- Python: `uv`, `.venv/`; `uv run pytest`.
- Users: `~/Papers/paper-odca-des` (switched), `paper-lc-logistic` (logistic runs switched 2026-10-03), `paper-odca-platoon`, `paper-odca-adaptive-platoon` (frozen copies until they switch, paper-odca-des BACKLOG B6).
- License: MIT (paper-odca-des:D-2026-09-19-10).
