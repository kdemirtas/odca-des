# HANDOVER: odca-des
Type: generic
Resume point. Full detail in `STATUS.md` (top blockquote); shape of the code in `ARCHITECTURE.md`.

## CURRENT: release 0.3.0 merged, not yet tagged (2026-11-09)
- `main` is 0.3.0: `pyproject.toml`, `uv.lock`, `.zenodo.json`; CHANGELOG 0.3.0 section (PR #42
  to #45 and the release PR); D-2026-11-09-1. Still to do: tag `v0.3.0` on the release PR's merge commit, publish
  the GitHub release `odca-des 0.3.0`, add `## Unreleased` back to CHANGELOG, check the
  Zenodo version appears under concept 23117203 (the webhook has not fired since it was
  re-created on 2026-11-03), and paper-odca-platoon cites the new version DOI.

## Earlier: platoon formation fixes and ring m-bar count, shipped (2026-11-09)
- A member split off for its exit is not grouped again (D-2026-11-08-5); a solo vehicle joins a
  platoon next to it, `total_joins` (D-2026-11-08-6); the m-bar section count counts every lap on
  a ring (D-2026-11-08-7). Every platooning output moved: the paper_odca_platoon golden is
  re-recorded (destination splits 140 to 40, m-bar 1.477 to 1.555); the other papers' goldens and
  full-output digests are identical (`tests/output_digest.py`, 43 runs).
- Earlier, also unreleased: ring roads with exits (D-2026-11-08-1 to -4), train platooning
  (D-2026-11-05-1 to -6). Untested on a ring: vehicles longer than one cell, incidents,
  `stops_for_offramp`, demand through origins, `train_lane_changes` across cell 0.
- Releases: 0.1.0 tagged at `23bbe99` (Zenodo 10.5281/zenodo.23117204); 0.2.0 tagged at `b7ba611`
  (Zenodo 10.5281/zenodo.23923633, D-2026-11-03-1), cited by two papers under review and must not
  move; 0.3.0 merged, tag pending (D-2026-11-09-1).
- paper-odca-des and paper-lc-logistic install this package editable, so they follow `main`;
  their goldens in `tests/golden/` hold their numbers. Vehicle length is `VehicleConfig.length`,
  default 1 (D-2026-10-03-8 to -10).
**RESUME:** tag `v0.3.0` on the release PR's merge commit and publish the GitHub release
`odca-des 0.3.0`; check Zenodo, then paper-odca-platoon cites the version DOI. Still open:
A-2026-10-03-3 to -5, A-2026-11-05-1, -2.
BACKLOG: B15, B12, B1; B16 and B17 ready to promote; B3 (PyPI) last.

## NEXT STEPS (pick up here)
None ranked. A capability a paper needs is added here, off by default, with its golden
(paper-odca-des:D-2026-09-19-6).

## Infra
- Repo: `kdemirtas/odca-des` (kdemirtas, public since 2026-09-22); push with `GH_TOKEN=$(gh auth token --user kdemirtas)`.
- Python: `uv`, `.venv/`; `uv run pytest`.
- Users: `~/Papers/paper-odca-des` (switched), `paper-lc-logistic` (logistic runs switched 2026-10-03), `paper-odca-platoon` (switched 2026-11-05), `paper-odca-adaptive-platoon` (frozen copy until it switches, paper-odca-des BACKLOG B6).
- License: MIT (paper-odca-des:D-2026-09-19-10).
