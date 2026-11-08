# HANDOVER: odca-des
Type: generic
Resume point. Full detail in `STATUS.md` (top blockquote); shape of the code in `ARCHITECTURE.md`.

## CURRENT: ring roads with exits on branch `claudine/2026-11-08-205548-odca-des` (2026-11-08)
- `NetworkConfig.ring`, off by default (D-2026-11-08-1), for paper-odca-platoon's ring runs with
  exits (its D-2026-11-08-6). Committed, not pushed: shipping waits for Kerem's OK.
- Proof: `uv run pytest`: 173 passed, 3 skipped (viewer extra), all three goldens exact.
  `tests/output_digest.py` on main's code (`--base`, a copy at `build/base`, git-ignored) and on
  the branch: 43 runs (every golden run, the 13 platoon scenarios, a `make_periodic` ring),
  36,964 vehicles, 20,071,825 trajectory records, identical. Only the config echo gains `ring: false`.
- Open calls: A-2026-11-08-1 to -3. Kerem picks the release number; 0.2.0 does not move.
- Untested on a ring: vehicles longer than one cell, incidents, `stops_for_offramp`, demand
  entering through origins (the tests place vehicles), `train_lane_changes` across cell 0.

## Before that: train platooning added on branch `claudine/2026-11-05-platoon-loop` (2026-11-05)
- `odca.platoon`, off by default (D-2026-11-05-1, -3 to -6; option B of the paper's M3-2 is D-2026-11-05-6); paper-odca-platoon switched over with
  its golden (D-2026-11-05-2). Every earlier golden unchanged. Open calls: A-2026-11-05-1, -2.
- Untested: platooning on a ring road (`make_periodic`), with incidents (a platoon facing a blocked
  lane with `train_lane_changes` off cannot leave it as a unit), with vehicles longer than one cell.

## Before that: release 0.2.0 merged, not yet tagged (2026-11-03)
- `main` is 0.2.0 (`pyproject.toml`, `uv.lock`, `.zenodo.json`; D-2026-11-03-1). No number moved
  since 0.1.0. The tag and GitHub release are not made yet. Publishing the release makes the
  Zenodo GitHub link add 0.2.0 under concept 23117203, metadata from `.zenodo.json`.
- CHANGELOG has no `## Unreleased` heading until the tag exists: add it back after tagging.
- A vehicle holds as many cells as its length: `VehicleConfig.length`, default 1
  (D-2026-10-03-8). The body follows the front through a lane change; no second lane change
  while the body is in two lanes, and the body drives out behind the front at the exit
  (D-2026-10-03-9). Length above 1 is refused with `stops_for_offramp` on (D-2026-10-03-10, B17).
- Every golden is unchanged at length 1. Open calls of mine: A-2026-10-03-3 (whole cells), -4
  (the rear cell's lock opens tau after the front takes its next cell), -5 (the front is the
  position, metrics stay on the front).
- Not tested at length above 1: ring road, lane-change patience failure, lateral escape,
  autonomous drivers, a vehicle reaching its destination before its full length is on the road.
- 0.1.0 is tagged at `23bbe99`, Zenodo 10.5281/zenodo.23117204. One `main` (D-2026-10-03-7).
- paper-odca-des and paper-lc-logistic install this package as an editable path dependency, so
  they follow `main`, not a tag. Their goldens in `tests/golden/` are what hold their numbers.
- Backlog trimmed by Kerem on 2026-10-03: B5 to B9 and B14 dropped. `dlc_requires_advantage`
  goes at the last paper's switch-over (D-2026-10-02-1, B13).
**RESUME:** tag `v0.2.0` on the release PR's merge commit and publish the GitHub release
`odca-des 0.2.0`; then both papers cite the new version DOI. Kerem closes A-2026-10-03-3 to -5. BACKLOG:
B15 (saturation flow, remeasure first), B12, B1; B16 (mixed fleet) and B17 are ready to promote;
B3 (PyPI) last. B2 and B13 wait on the platoon papers (paper-odca-platoon switched 2026-11-05; adaptive-platoon still frozen).

## NEXT STEPS (pick up here)
None ranked. A capability a paper needs is added here, off by default, with its golden
(paper-odca-des:D-2026-09-19-6).

## Infra
- Repo: `kdemirtas/odca-des` (kdemirtas, public since 2026-09-22); push with `GH_TOKEN=$(gh auth token --user kdemirtas)`.
- Python: `uv`, `.venv/`; `uv run pytest`.
- Users: `~/Papers/paper-odca-des` (switched), `paper-lc-logistic` (logistic runs switched 2026-10-03), `paper-odca-platoon` (switched 2026-11-05), `paper-odca-adaptive-platoon` (frozen copy until it switches, paper-odca-des BACKLOG B6).
- License: MIT (paper-odca-des:D-2026-09-19-10).
