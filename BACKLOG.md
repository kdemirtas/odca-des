# BACKLOG: odca-des

Parked ideas and decisions, not committed work. One entry each: what, why, and the trigger that
promotes it to HANDOVER's NEXT list. Committed and ordered work lives in `HANDOVER.md`; what was
decided lives in `DECISIONS.md`; what shipped lives in `CHANGELOG.md`. Promotion is Kerem's call
at `/pickup`, which lists the entries whose trigger is now true.

| # | what | why | trigger | parked |
|---|---|---|---|---|
| B1 | Engine support for density-initialised and ring-road starts, so paper scripts stop building simulations below the engine | paper-odca-des BACKLOG B1 | the engine next gains an initial-condition feature | 2026-09-19 |
| B2 | Bring the other papers' additions in (`lc_events`, `platoon/`), off by default, with their goldens | paper-odca-des D-2026-09-19-6, BACKLOG B6 | each paper's switch-over | 2026-09-19 |
| B3 | Publish to PyPI (name `odca-des` free on 2026-09-19) | D-2026-09-19-6: published with the first paper | paper-odca-des is submitted | 2026-09-19 |
| B4 | (promoted 2026-09-19 into D-2026-09-19-23/-24 and HANDOVER N2 to N4) | | | 2026-09-19 |
| B5 | Several `AutonomousController`s, one per road segment, with AV handover between them (roadside-unit model) | Kerem, 2026-09-19; a model feature, not a speed-up (D-2026-09-19-24) | a platoon paper needs limited-range control | 2026-09-19 |
| B6 | v2 kernel: replace SimPy with an own event loop (heap of timed callbacks, no generator processes), optionally segment-parallel with the minimum cell travel time as lookahead | Kerem, 2026-09-19; S1 seed 1 is about 2.25M SimPy events; seeds already run in parallel processes | a paper needs runs that one core cannot finish, or profiling shows SimPy overhead dominates after N8 | 2026-09-19 |
