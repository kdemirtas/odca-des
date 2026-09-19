# Lane-change probability and evaluation frequency

Decision D-2026-09-19-22. Candidate contribution for the lane-change paper (paper-lc-logistic),
with a short note in paper-odca-des where it introduces lane changing.

## The problem

The logistic MLC and DLC curves return a probability p. If p is applied at every evaluation, the
chance that a vehicle changes lane over a stretch of road depends on how often it evaluates:

    P(no change over n evaluations) = (1 - p)^n

An AV evaluates at 10 Hz, an HDV every action interval (about 1 s, faster in congestion because
neighbours wake it). So the same curve makes AVs and congested HDVs merge much earlier than
free-flow HDVs. Measured as the remaining-distance ratio r at which half the vehicles have
attempted the mandatory change:

| rule | free-flow HDV | congested HDV | AV (10 Hz) |
|---|---|---|---|
| p per evaluation | 0.60 | higher | 0.85 |
| p per second | 0.60 | 0.78 | 0.60 |
| p per 5.2 cells driven | 0.60 | 0.60 | 0.60 |

Per second removes the evaluation-rate effect but not the speed effect: a slow vehicle spends
more seconds per cell. Per distance removes both, which is what a mandatory change needs (the
exit is a place, not a time).

## The rule

Treat p as the probability per unit of exposure (a constant hazard) and convert it over the
exposure x since the vehicle's previous evaluation:

    q = 1 - (1 - p)^x

- MLC: x = cells driven / 5.2. The reference 5.2 cells is one second at v_max, so a free-flow HDV
  evaluating once per second sees q = p and keeps its old calibration.
- DLC: x = seconds elapsed. A discretionary change is a response to a speed advantage that lasts
  in time, so per second is its natural unit. The 10 s cooldown stays as a refractory period:
  exposure is not banked through it.
- Safe ends: p = 1 (a forced change) stays 1 for any x; x = 0 gives 0.

Splitting one evaluation into k steps gives the same total: (1 - p)^(x/k * k) = (1 - p)^x, so the
outcome is independent of the evaluation rate by construction.

## A finding for the lane-change paper

The DLC curve gives p = 0.047 per second even at zero speed advantage (dv = 0). That is one
discretionary change about every 21 s per vehicle, or every 31 s with the cooldown, with nothing to
gain. The curve's offset should be reconsidered (or a dv threshold added) when paper-lc-logistic
recalibrates it.

## Effect on the quick golden

All 24 quick runs moved. Seed 1, old -> new: S1 lane changes 231 -> 235, mean delay 30.8 -> 29.1;
S4 (high AV) delay 9.08 -> 10.4; bottleneck 0% AV delay 69 -> 74.5, 70% AV 5.17 -> 5.06.

## Audit after the one-request fix (2026-09-19, D-2026-09-19-31)
Lane changes per vehicle-km, counted from trajectories ("away" = a change that moves a vehicle
away from the lane its destination needs):

| run | before the fix | after | after, and no DLC away from a needed lane | after, and DLC only toward a faster lane | both |
|---|---|---|---|---|---|
| demo corridor (3 lanes, every lane to every lane end) | 4.36 | 1.58 | 1.39 | 1.06 | 0.94 |
| S1, 900 s, seed 1 | 3.89 | 2.27 | 1.49 | 1.94 | 1.23 |

After the fix, S1 still makes about 2.3 lane changes per vehicle-km, and about 45% of them move away
from the needed lane: mostly the zero-advantage DLC rate above (0.047/s at dv = 0), with the MLC
then bringing the vehicle back. The two columns on the right are candidate rules, not adopted:
both change the model the paper describes, so they are Kerem's call (paper-odca-des AGENDA).
