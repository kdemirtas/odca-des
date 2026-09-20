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
| B7 | Event-driven AV decisions (only when a neighbour changes) or a coarser free-flow tick; exact slow-path arrival instead of 0.25 s sub-steps | code review B6, B8: the main costs left, but both move every number | the next rerun that is allowed to move numbers | 2026-09-19 |
| B8 | Delayed release as a plain `env.timeout(tau)` callback instead of a process; block-buffered uniform draws per stream | code review B7, B13: about 10 s and 3 s per run; the golden decides whether ties reorder | a perf pass with the golden as judge | 2026-09-19 |
| B9 | Columnar trajectory storage (about 25 instead of 192 bytes per record); columnar incident JSON; drop the unread `fd_data`; one-pass Edie windows | code review C1, C7, C8, B10: memory 0.55-0.75 GB per S1-S4 process | memory becomes the limit (the 20-seed rerun on 12 cores, or the 3,200-cell scalability run) | 2026-09-19 |
| B12 | Investigate whether the lane-change patience timeout is reachable: `lc_patience_failures` is 0 in all 24 golden runs while `gap_rejections` is 306,335, because `accepts_gap` refuses an occupied or locked cell before the request is made, so the 3 s patience can only fire in a same-instant race. Either the counter and the patience parameter do nothing, or the gap check is refusing cases the patience was meant to hold for | found when the counter was split, D-2026-09-20-12 | a paper needs the patience parameter, or the lane-change rate question is reopened | 2026-09-20 |
