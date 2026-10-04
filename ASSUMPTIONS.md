# ASSUMPTIONS: odca-des

Every call I made on my own, in or out of a loop: a guess the docs did not settle, a default I
picked, a definition I chose. Provisional, never cited by code. Kerem reads the open rows each
session (`/pickup` lists them, `/next-assumption` walks them one at a time) and closes each one of
two ways: accepted as is, or corrected. Both end the same way: the call becomes a `DECISIONS.md`
entry whose `Source` column names this row (`accepted A-…` or `corrected A-…`), and the row leaves
this file. Nothing stays here once it has been discussed.

| Id | Made | What I assumed | Why | What would change it | Status |
|---|---|---|---|---|---|
| A-2026-10-03-3 | 2026-10-03 | `VehicleConfig.length` is a whole number of cells, 1 or more; a length in metres is converted by the paper | Units inside `odca` are cells, and a cell is held or not held: a vehicle of 1.5 cells would hold 2 | Kerem wants lengths in metres in the config, or a vehicle shorter than a cell | open |
| A-2026-10-03-4 | 2026-10-03 | The rear cell's lock opens tau after the front takes its next cell, which is the present rule applied to the rear; a vehicle enters holding the origin cell alone and grows to its length over its first moves, and leaves by giving up its cells from the rear as it drives out | At length 1 this is the present rule exactly, so the goldens cannot move; needing `length` free cells at the origin would change how a metered entry fills | Kerem wants the lock to open tau after the rear has physically left the cell, or a long vehicle to need its whole length free before it enters | open |
| A-2026-10-03-5 | 2026-10-03 | `Vehicle.cell` stays the front cell and every held cell carries the vehicle's label, so a follower's spacing and a lane changer's gap are measured to the nearest held cell (the leader's rear). The trajectory and every metric stay on the front: one record per front arrival, a long vehicle counts as one vehicle | Decisions look ahead from the front; `find_leader` and `find_follower` already stop at the first labelled cell; a front-based trajectory leaves flow and Edie's definitions unchanged at length 1 | A paper reports occupancy or density by held cells, which needs the rear passage recorded too | open |
