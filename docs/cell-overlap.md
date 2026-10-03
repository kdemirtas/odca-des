# Two vehicles in one cell: what the lock timing allows

Found on 2026-10-02 while writing the test for invariant 1 of `ARCHITECTURE.md` (one vehicle per
cell). Closed the same day by D-2026-10-02-4: the lock is no longer released while the vehicle is
still in the cell. The rest of this note is the evidence, measured before that change.

## What happened before the change
`Vehicle._advance_to` took the next cell, then calls `_delayed_release` on the cell the vehicle
is still in, then crosses that cell. The lock therefore opens tau seconds after the next cell was
taken, not tau seconds after the vehicle left. A vehicle that needs longer than tau to cross (slower
than 1/tau, about 0.67 cells/s at the human tau of 1.5 s) is still in the cell when its lock opens.
The vehicle behind takes the cell, arrives, and overwrites `cell.vehicle`. For that time the first
vehicle is in the cell but no neighbour sees it: `find_leader`, `find_follower` and `accepts_gap`
read `cell.vehicle`.

One case, S1 quick run, seed 1, lane 1, cell 443: the first vehicle stays 4.63 s, the second takes
the cell 1.64 s after the first arrived (the first one's tau) and the two share the cell for 2.68 s.

The lock itself never has two holders: `Cell.resource` has capacity 1. What overlaps is position.

## How often, and what a later release would move
The 24 golden runs (quick mode, seeds 1 to 3), as they are and with the lock opened tau after the
vehicle has left the cell (a patch applied outside the package, at commit a688c9b; its unpatched
runs reproduced `fingerprint.json`). Means over the three seeds; overlaps and passages
are sums.

| scenario | overlaps / passages today | with the later release | throughput veh/h | delay s | lane changes per veh-km | never entered |
|---|---|---|---|---|---|---|
| S1_baseline | 246 / 776,098 | 0 / 760,133 | 3204.4 to 3111.1 | 24.4 to 25.0 | 1.5 to 1.2 | 10.0 to 22.0 |
| S2_low_av | 137 / 827,126 | 0 / 802,581 | 3448.9 to 3373.3 | 19.0 to 20.2 | 1.2 to 1.0 | 4.3 to 7.7 |
| S3_med_av | 64 / 881,717 | 0 / 871,486 | 3853.3 to 3728.9 | 13.2 to 15.0 | 0.9 to 0.8 | 1.3 to 3.3 |
| S4_high_av | 28 / 913,199 | 0 / 908,334 | 4155.6 to 4017.8 | 8.0 to 8.8 | 0.6 to 0.5 | 1.0 to 1.7 |
| BN_0av | 1,434 / 930,352 | 0 / 913,751 | 2417.8 to 2440.0 | 74.4 to 75.8 | 0.7 to 0.5 | 0.0 to 0.0 |
| BN_30av | 835 / 1,003,421 | 0 / 977,401 | 3028.9 to 2926.7 | 40.1 to 44.8 | 0.6 to 0.5 | 0.0 to 0.0 |
| BN_50av | 116 / 1,040,013 | 0 / 1,028,209 | 3451.1 to 3391.1 | 12.6 to 18.0 | 0.4 to 0.3 | 0.0 to 0.3 |
| BN_70av | 36 / 1,043,439 | 0 / 1,041,370 | 3520.0 to 3495.6 | 4.6 to 6.2 | 0.2 to 0.2 | 0.0 to 0.0 |

The later release removes every overlap. It also lengthens every headway by the crossing time, at
all speeds, so it is a different model and not only a repair at crawl speed: throughput falls by 1
to 4% in seven of the eight scenarios and delay rises in all eight. These are quick runs of 300 s
and 600 s on three seeds, not the paper's 3,600 s on 20; the seed-to-seed spread was not computed.

## Adopted (2026-10-02)
Neither of the two above: the lock opens tau after the next cell is taken, as before, and waits
for the vehicle to leave when the crossing takes longer than tau (D-2026-10-02-4). A vehicle at
free flow leaves after 0.19 s and is released at 1.5 s as before, so the floor stays 1.692 s; the
crawling vehicle of the case above keeps cell 443 until it leaves at 4.63 s. Overlaps in the 24
golden runs: 0. What the golden moved by is in the decision entry.

## Related, not explained
Single lane, human defaults with no spread and no random slowdown, one hour: the smallest gap
between two vehicles is exactly tau + d / v_max = 1.692 s, but the lane saturates near 1,350 veh/h
(1,345 to 1,353 at demands of 1,600 to 2,500), against the 2,127 veh/h that the floor implies.
The mean gap at saturation is about 2.66 s. Why was not traced.
A vehicle is placed in its origin cell rather than crossing into it, so at cell 0 the smallest
gap is tau alone, 1.5 s.

## Replaced the same day (D-2026-10-02-6)
The rule adopted above also lengthened steady headways below 1/tau (two crossing times instead of
tau plus one) and lowered the ring road's congested branch by about 19%. Now the lock opens tau
after the next cell is taken, whatever the crossing time, and the vehicle that takes the lock waits
at the cell boundary until the one ahead has left. Overlaps stay at 0; two vehicles at the same
speed keep tau + d / v at every speed. Measurements in the decision entry.
