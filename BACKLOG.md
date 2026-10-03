# BACKLOG: odca-des

Parked ideas and decisions, not committed work. One entry each: what, why, and the trigger that
promotes it to HANDOVER's NEXT list. Committed and ordered work lives in `HANDOVER.md`; what was
decided lives in `DECISIONS.md`; what shipped lives in `CHANGELOG.md`. Promotion is Kerem's call
at `/pickup`, which lists the entries whose trigger is now true.

| # | what | why | trigger | parked |
|---|---|---|---|---|
| B1 | Engine support for density-initialised and ring-road starts, so paper scripts stop building simulations below the engine {T2, priority M} | paper-odca-des BACKLOG B1 | the engine next gains an initial-condition feature | 2026-09-19 |
| B2 | Bring the other papers' additions in (`platoon/`; `lc_events` is done, D-2026-10-03-1), off by default, with their goldens {T3, priority M} | paper-odca-des:D-2026-09-19-6, BACKLOG B6 | each paper's switch-over | 2026-09-19 |
| B3 | Publish to PyPI (name `odca-des` free on 2026-09-19) {T4, priority L} | paper-odca-des:D-2026-09-19-6: published with the first paper | paper-odca-des is submitted | 2026-09-19 |
| B4 | (promoted 2026-09-19 into D-2026-09-19-23/-24 and HANDOVER N2 to N4) | | | 2026-09-19 |
| B5 | (dropped 2026-10-03, Kerem: several `AutonomousController`s, one per road segment, with AV handover between them; idea I2 asks the same question more broadly) | | | 2026-09-19 |
| B6 | (dropped 2026-10-03, Kerem: v2 kernel; no paper hit the one-core limit; ideas I1 and I3 would redesign the cell lock first) | | | 2026-09-19 |
| B7 | (dropped 2026-10-03, Kerem: event-driven AV decisions; it moves every number, and 0.1.0 is archived) | | | 2026-09-19 |
| B8 | (dropped 2026-10-03, Kerem: delayed release as a plain `env.timeout(tau)` callback instead of a process; its estimate predates D-2026-10-02-6; idea I3 would rewrite this code) | | | 2026-09-19 |
| B9 | (dropped 2026-10-03, Kerem: columnar trajectory storage; the 124-job rerun finished with 0 failed, memory was not the limit) | | | 2026-09-19 |
| B12 | Investigate whether the lane-change patience timeout is reachable: `lc_patience_failures` is 0 in all 24 golden runs while `gap_rejections` is 306,335, because `accepts_gap` refuses an occupied or locked cell before the request is made, so the 3 s patience can only fire in a same-instant race. Either the counter and the patience parameter do nothing, or the gap check is refusing cases the patience was meant to hold for {T5, priority M} | found when the counter was split, D-2026-09-20-12 | a paper needs the patience parameter, or the lane-change rate question is reopened | 2026-09-20 |
| B13 | Delete `dlc_requires_advantage` and make DLC only toward a faster lane the one rule, re-recording any golden that ran with it off {T6, priority M} | D-2026-10-02-1: the flag's removal date | the last of paper-lc-logistic, paper-odca-platoon and paper-odca-adaptive-platoon has switched over, and none recorded a need for the old rule | 2026-10-02 |
| B14 | (dropped 2026-10-03, Kerem: give the cell lock a typed owner; its trigger was B6 or B8, both dropped; idea I3 would cover it) | | | 2026-10-02 |
| B15 | Explain why a saturated single lane carries about 1,350 veh/h (mean gap 2.66 s) when the headway floor tau + d / v_max allows 2,127; the gap is close to tau plus one action interval plus the crossing time, untested {T7, priority M} | `docs/cell-overlap.md`, found with invariant 2's test, D-2026-10-02-4 | a paper quotes a single-lane capacity, or the fundamental diagram is revisited | 2026-10-02 |
| B16 | Vehicle classes with a share each (cars and buses in one run), the class drawn per vehicle from a new stream spawned last {T8, priority M} | D-2026-10-03-8 puts one length on all human-driven vehicles and one on all autonomous ones; a mixed fleet was left out of T1 (Kerem, 2026-10-03) | a paper needs a mixed fleet | 2026-10-03 |
| B17 | Let a vehicle longer than one cell run with `stops_for_offramp`: decide what it does when its front is held at the stop line with its body in two lanes {T9, priority M} | D-2026-10-03-10 refuses the combination; the stop line and the one-lane-change-at-a-time rule (D-2026-10-03-9) block each other | a paper needs long vehicles on a road with off-ramps and the stop line on | 2026-10-03 |
