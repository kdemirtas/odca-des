# HANDOVER: odca-des
Type: generic
Resume point. Full detail in `STATUS.md` (top blockquote); shape of the code in `ARCHITECTURE.md`.

## CURRENT: N2 shipped with YAML, named places, endpoint cells, incidents (2026-09-19)
- Decisions D-2026-09-19-23, -25 to -29; golden re-recorded (every run moved with the new S1 demand).
- Open: assumptions A-1 to A-7, A-9 to A-11; paper-odca-des N11 restates the numbers.
**RESUME:** N3, one trait sampler (`DriverTraits`) in `odca/entity/driver.py`.

## NEXT STEPS (pick up here)
Ranked; proof for each: `uv run pytest` (goldens may be re-recorded during the refactor; say what moved).

1. **N3. One trait sampler** in `odca/entity/driver.py`: `DriverTraits` drawn once per driver (copies in `generator.py`, `engine.py`, two paper scripts go); fix the stale per-vehicle RNG docstrings.
2. **N4. Driver split** (D-2026-09-19-24): `Vehicle(cfg, driver, env, route)` keeps the physical process; `HumanDriver`, `AutonomousDriver`, `AutonomousController` own the decisions and the decision state; class constants become config fields; `HDV`/`AV` and the type switches go. Inits at 6 parameters or fewer.
3. **N5. `SimulationResult` dataclass**, carrying the resolved config (`save_config`).
4. **N6. `odca.experiment` kit** and `odca.analysis.mean_ci95` (paper-odca-des D-2026-09-19-9).
5. **N7. Viewers into `odca.viewer`** (from paper-odca-des `visualize.py`, `animate.py`).
6. **N8. Opus code review findings** (paper-odca-des session 2026-09-19, report copied to `docs/code-review-2026-09-19.md`), triaged with Kerem; correctness findings jump ahead.

## Infra
- Repo: `kdemirtas/odca-des` (kdemirtas, private until publication with paper-odca-des); push with `GH_TOKEN=$(gh auth token --user kdemirtas)`.
- Python: `uv`, `.venv/`; `uv run pytest`.
- Users: `~/Papers/paper-odca-des` (switched), `paper-lc-logistic`, `paper-odca-platoon`, `paper-odca-adaptive-platoon` (frozen copies until they switch, paper-odca-des BACKLOG B6).
- License: MIT (paper-odca-des D-2026-09-19-10).
