# ASSUMPTIONS: odca-des

Every call I made on my own, in or out of a loop: a guess the docs did not settle, a default I
picked, a definition I chose. Provisional, never cited by code. Kerem reads the open rows each
session (`/pickup` lists them, `/next-assumption` walks them one at a time) and closes each one of
two ways: accepted as is, or corrected. Both end the same way: the call becomes a `DECISIONS.md`
entry whose `Source` column names this row (`accepted A-…` or `corrected A-…`), and the row leaves
this file. Nothing stays here once it has been discussed.

| Id | Made | What I assumed | Why | What would change it | Status |
|---|---|---|---|---|---|
| A-2026-10-03-1 | 2026-10-03 | The lane-change log (`Vehicle.lane_changes`) is always written, with no config switch, and a lane-change request without a reason is an error | A log draws no random number, so it cannot move a golden, and a switch would need its own removal date; a required reason makes MLC + DLC = total hold by construction | Kerem wants it off by default like other paper capabilities (memory: one small record per lane change), or wants the reason optional for hand-built drivers | open |
| A-2026-10-03-2 | 2026-10-03 | The human driver class of a run is chosen by the type of its `lane_change` config: a `HumanDriver` subclass registers itself for a lane-change family member (`lane_change_config`) | The lane-change config is already a family chosen by `model`, so the saved config alone reruns the run; a `Simulation` argument naming the class would not be in the config | Kerem prefers an explicit argument, or wants MOBIL and Gipps inside `odca/baselines/` instead of in the paper | open |
