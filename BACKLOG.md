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
| B10 | Record when a vehicle is created, and report the mean wait at the origin and how many vehicles never got on the road beside travel time | Kerem prefers the queue before entry visible rather than folded into travel time (D-2026-09-20-2); an S1 probe measured a 21.9 s mean wait and 117 of 2,330 vehicles never admitted | the next run that regenerates the S1-S4 and bottleneck result files | 2026-09-20 |
| B11 | Read the target cell's limit when timing its traversal, so a speed-limit change takes effect at the sign instead of one cell later | a vehicle crosses a cell at the speed it chose on arriving in the previous one; at a work-zone boundary that is 0.577 s gained on entry and 0.577 s lost on exit, which per-cell clipping reports as delay (D-2026-09-20-3) | a scenario posts a limit that varies along the road (work zone, variable speed limit) | 2026-09-20 |
