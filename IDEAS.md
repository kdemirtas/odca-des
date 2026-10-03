# IDEAS: odca-des

Thoughts worth discussing that are not tasks yet: no shape, no trigger, no owner. `/idea <text>`
records one here and says nothing else; the discussion happens when `/pickup` lists an entry whose
"raise when" reads true, or when Kerem asks. `/add-task` turns a discussed idea into a BACKLOG row
or a NEXT item and marks the entry. Nothing here is committed work.

| # | idea | why it came up | raise when | state | noted |
|---|---|---|---|---|---|
| I1 | What if we add vehicle lengths and let a single vehicle hold multiple cells at the same time. Now we are interested in both the rear and front position of the vehicle. So long vehicles like buses can occupy 3 cells at the same time depending on cell length. This can further be extended to the platoon idea: a platoon holds multiple cells by definition. | Kerem, 2026-10-03, during the paper-lc-logistic rerun, after the lane-change diagnosis showed 66% of refused gap checks came from a cell still locked by the vehicle that had just left it | next pickup of odca-des, or when either platoon paper moves onto the package | open | 2026-10-03 |
| I2 | Separate autonomous controller vs autonomous single driver responsibilities. | Kerem, 2026-10-03, during the paper-lc-logistic rerun, right after I1 (vehicles and platoons holding several cells) | next pickup of odca-des, or when either platoon paper moves onto the package | open | 2026-10-03 |
| I3 | How about a vehicle's front seizes a cell but its rear releases it with delay? | Kerem, 2026-10-03, during the paper-lc-logistic rerun, right after I1 (a vehicle holding several cells, front and rear positions both tracked) | next pickup of odca-des, or when I1 is discussed | open | 2026-10-03 |
