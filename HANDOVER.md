# HANDOVER: odca-des
Type: generic
Resume point. Full detail in `STATUS.md` (top blockquote); shape of the code in `ARCHITECTURE.md`.

## CURRENT: N4 driver split shipped (2026-09-19)
- Decisions to D-2026-09-19-30; golden unchanged since D-2026-09-19-26.
- Open: assumptions A-1 to A-7, A-9 to A-14; paper-odca-des N11 restates the numbers.
**RESUME:** N4b, one lane-change request makes one lane change (golden moves), then N5.

## NEXT STEPS (pick up here)
Ranked; proof for each: `uv run pytest` (goldens may be re-recorded during the refactor; say what moved).

1. **N4b. One lane-change request, one lane change**: `Vehicle._advance_to` resets the request after a lateral move; re-record the golden and state what moved.
2. **N5. `SimulationResult` dataclass**, carrying the resolved config (`save_config`).
3. **N6. `odca.experiment` kit** and `odca.analysis.mean_ci95` (paper-odca-des D-2026-09-19-9).
4. **N7. Viewers into `odca.viewer`** (from paper-odca-des `visualize.py`, `animate.py`).
5. **N8. Opus code review findings** (paper-odca-des session 2026-09-19, report copied to `docs/code-review-2026-09-19.md`), triaged with Kerem; correctness findings jump ahead.

## Infra
- Repo: `kdemirtas/odca-des` (kdemirtas, private until publication with paper-odca-des); push with `GH_TOKEN=$(gh auth token --user kdemirtas)`.
- Python: `uv`, `.venv/`; `uv run pytest`.
- Users: `~/Papers/paper-odca-des` (switched), `paper-lc-logistic`, `paper-odca-platoon`, `paper-odca-adaptive-platoon` (frozen copies until they switch, paper-odca-des BACKLOG B6).
- License: MIT (paper-odca-des D-2026-09-19-10).
