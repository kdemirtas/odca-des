# ASSUMPTIONS: odca-des

Every call I made on my own, in or out of a loop: a guess the docs did not settle, a default I
picked, a definition I chose. Provisional, never cited by code. Kerem reads the open rows each
session (`/pickup` lists them, `/next-assumption` walks them one at a time) and closes each one of
two ways: accepted as is, or corrected. Both end the same way: the call becomes a `DECISIONS.md`
entry whose `Source` column names this row (`accepted A-…` or `corrected A-…`), and the row leaves
this file. Nothing stays here once it has been discussed.

| Id | Made | What I assumed | Why | What would change it | Status |
|---|---|---|---|---|---|
| A-2026-09-19-1 | 2026-09-19 | Segment-end vehicles placed at t=0 (bottleneck, incident) also exit from any lane | tex:874 speaks of segment-end vehicles generally | the paper means only generated traffic | open |
| A-2026-09-19-2 | 2026-09-19 | Travel time starts when the origin cell is taken; time queued before entry is not counted (in S1 many vehicles still wait at the origin at t=3600) | tex:974 "from entry to exit" | Kerem wants origin queueing in travel time or reported separately | open |
| A-2026-09-19-3 | 2026-09-19 | v_f in the delay is the vehicle's own v_max; the last cell before exit is not counted; cells with a lower speed limit still count as delay | tex:975 names v_f without defining it per vehicle | v_f meant as the network speed limit | open |
| A-2026-09-19-4 | 2026-09-19 | A vehicle's position (label) moves at arrival T_arr; the lock stays with delayed release | tex:221, 255 record position at T_arr | none expected | open |
| A-2026-09-19-9 | 2026-09-19 | Origin and destination names are readable (`mainline_lane_<n>`, `onramp_<k>`, `offramp_<k>`, `end_lane_<n>`) instead of the dissertation's letters (1-4, O1, A-D, F1) | YAML is read without a legend; the paper can still print letters | Kerem wants the dissertation letters in the configs | open |
| A-2026-09-19-10 | 2026-09-19 | An `end` destination (segment end, any lane) stays available beside the per-lane ends; the lane-drop bottleneck, incident and scalability runs use it | in the bottleneck, lane 3 is closed to the last cell, so its vehicles cannot end in lane 3 | Kerem wants every run on per-lane ends | open |
| A-2026-09-19-11 | 2026-09-19 | A vehicle that reaches the last cell outside its end lane leaves anyway and is counted in `missed_exits`, as a missed off-ramp is (dissertation 4.3 "Success Flag") | it cannot go further; the dissertation reports these as exit failures | Kerem wants it kept on the road or rerouted | open |
| A-2026-09-19-6 | 2026-09-19 | The MLC reference distance is 5.2 cells (one second at v_max), so a free-flow HDV keeps its old calibration; the DLC reference is 1 s | the curves were fitted per decision of a free-flow driver | a different calibration target (e.g. per cell) |  open |
| A-2026-09-19-7 | 2026-09-19 | A vehicle's first direction evaluation after entry has zero exposure, so only a forced change (p = 1) can fire then; exposure resets at every evaluation, including the ones inside the DLC cooldown | no exposure has accrued yet; the cooldown is refractory, it does not bank time | Kerem wants exposure counted from entry or banked through the cooldown | open |
| A-2026-09-19-5 | 2026-09-19 | An occupied or locked target cell is a failed lane-change attempt, counted in lc_failures | same counting as other safety failures | lc_failures meant to count only gap failures | open |
