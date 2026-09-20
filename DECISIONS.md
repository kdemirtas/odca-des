# DECISIONS: odca-des
> One entry per decision, newest first, never edited after the fact: a reversed decision gets a
> new entry that names the one it replaces. Ids are `D-YYYY-MM-DD-n`. Code that implements a
> decision cites the id; `/reviewer` checks the citation both ways. `Source` says where the
> decision came from: Kerem directly, an `ASSUMPTIONS.md` row he accepted or corrected (the row
> then leaves that file, `/next-assumption`), or another project's decision this one inherits.

| Id | Decided | What | Source | Replaces |
|---|---|---|---|---|
| D-2026-09-20-18 | 2026-09-20 | A cell's eight neighbour links are set when the road is built; code that reshapes a road afterwards relinks it (`Lane.make_periodic`, `Freeway.link_neighbours`) and no script writes `cell._next` | Kerem, accepted A-2026-09-19-19 | none |
| D-2026-09-20-17 | 2026-09-20 | A target cell that is occupied or locked is a failed lane-change attempt, counted with the gap failures in `gap_rejections`; it is not a separate kind | Kerem, accepted A-2026-09-19-5 | none |
| D-2026-09-20-16 | 2026-09-20 | The viewers take a `SimulationResult` (`TrafficVisualizer.from_result`, `animate_result`, `plot_trajectories`) instead of 7 to 11 arguments, and the time-space diagram joins consecutive records by lane rather than splitting on a 2 s time gap | Kerem, accepted A-2026-09-19-17 | none |
| D-2026-09-20-15 | 2026-09-20 | The experiment kit is `odca.experiment` (`RunRecord`, `run_once`, strict per-seed JSON that refuses a duplicate seed, aggregation into today's CSV schema) and `odca.analysis.mean_ci95` is the package's one 95% interval, Student t to 30 degrees of freedom and 1.96 above | Kerem, accepted A-2026-09-19-16 | none |
| D-2026-09-20-14 | 2026-09-20 | `Simulation.run()` returns a frozen `SimulationResult` (`config`, `vehicles`, `num_generated`, `counters`) with the completed and still-active counts derived and `config_yaml()` to rerun it; the result dict is gone and per-seed JSON keeps its keys | Kerem, accepted A-2026-09-19-15 | none |
| D-2026-09-20-13 | 2026-09-20 | `AutonomousController` with drivers registering at build time, vehicle kinds told apart by `vehicle.kind` (`"human"`, `"autonomous"`) instead of `vtype`, and one `VehicleFactory` for the generators and the t=0 vehicles; the config fields keep `av_`/`hdv_` | Kerem, accepted A-2026-09-19-14 | none |
| D-2026-09-20-12 | 2026-09-20 | The vehicle-to-driver link is the calls the vehicle already made (`evaluate_speed`, `evaluate_direction`, `sees_blockage`, `accepts_gap`, `merge_priority`, plus tau, action interval and patience), the vehicle counts moves and the driver counts decisions, and `lc_failures` becomes two stored counters, `lc_patience_failures` and `gap_rejections` | Kerem, accepted A-2026-09-19-13 with the counter split he asked for | none |
| D-2026-09-20-11 | 2026-09-20 | The eight old `Vehicle` class constants are config fields with their old values as defaults: the movement ones in `VehicleConfig`, the decision ones in `DriverConfig`, not one run-wide value in `SimConfig` | Kerem, accepted A-2026-09-19-12 | none |
| D-2026-09-20-10 | 2026-09-20 | Exposure starts at the first direction evaluation, which therefore carries none and can only fire a forced change, and it resets at every evaluation, including those inside the discretionary cooldown, which stays refractory rather than banking time | Kerem, accepted A-2026-09-19-7 | none |
| D-2026-09-20-9 | 2026-09-20 | The lane-change exposure references are one free-flow driver-second: `MLC_REFERENCE_CELLS` 5.2 cells (one second at v_max) for the mandatory curve, one second for the discretionary one, which is what the published curve parameters mean | Kerem, accepted A-2026-09-19-6 | none |
| D-2026-09-20-8 | 2026-09-20 | A vehicle that reaches the last cell outside its end lane leaves the network there and counts as a missed exit, the same counter a missed off-ramp increments; it is never held on the road or rerouted | Kerem, accepted A-2026-09-19-11 | none |
| D-2026-09-20-7 | 2026-09-20 | The any-lane destination `end` stays beside the per-lane ends; the lane-drop bottleneck, the incident and the scalability benchmark send all their demand and their placed vehicles to it, S1-S4 use the per-lane ends | Kerem, accepted A-2026-09-19-10 | none |
| D-2026-09-20-6 | 2026-09-20 | Origins and destinations keep readable names (`mainline_lane_<n>`, `onramp_<k>`, `offramp_<k>`, `end_lane_<n>`, `end`); the dissertation's letters stay in the dissertation and in the manuscript prose | Kerem, accepted A-2026-09-19-9 | none |
| D-2026-09-20-5 | 2026-09-20 | Occupancy is reported beside density: every trajectory record carries T_acq as well as T_arr, and the run reports the mean cells a vehicle holds, the wait at its origin and how many never got on | Kerem, corrected A-2026-09-19-4; closes BACKLOG B10 | none |
| D-2026-09-20-4 | 2026-09-20 | A speed limit takes effect on the cell that posts it: arriving in a cell whose limit differs, the driver picks the speed again before that cell is crossed; `react_now` and the driver interrupt are gone | Kerem, 2026-09-20 | none |
| D-2026-09-20-3 | 2026-09-20 | Free-flow speed is per vehicle and per cell, v_f(n, c) = min(v_max(n), v_lim(c)); delay is the per-cell excess over it, so a cell driven at a posted limit adds no delay | Kerem, corrected A-2026-09-19-3 | none |
| D-2026-09-20-2 | 2026-09-20 | Travel time is measured from the moment a vehicle takes its origin cell; the wait before that stays out of every reported metric. Kerem prefers it reported separately, which waits for the next run that regenerates the result files (BACKLOG B10) | Kerem, accepted A-2026-09-19-2 | none |
| D-2026-09-20-1 | 2026-09-20 | Vehicles placed on the road at t=0 follow the same destination rule as generated traffic: bound for the segment end, leaving from any lane | Kerem, accepted A-2026-09-19-1 | none |
| D-2026-09-19-35 | 2026-09-19 | Neutral speed-ups from the code review: cell neighbour links set once when the road is built, a per-lane count of closed cells, exited AVs dropped from the controller, dead code removed | ASSUMPTIONS A-2026-09-19-19, made unattended (orchestrate loop) | none |
| D-2026-09-19-34 | 2026-09-19 | Viewers live in `odca.viewer` and take a run result; the paper keeps two thin command-line scripts | ASSUMPTIONS A-2026-09-19-17, made unattended (orchestrate loop); implements paper-odca-des D-2026-09-19-9 | none |
| D-2026-09-19-33 | 2026-09-19 | Experiment kit `odca.experiment` (run records, strict per-seed JSON, aggregation) and the one interval `odca.analysis.mean_ci95`; papers keep only what they measure | ASSUMPTIONS A-2026-09-19-16, made unattended (orchestrate loop); implements paper-odca-des D-2026-09-19-9 | none |
| D-2026-09-19-32 | 2026-09-19 | `Simulation.run()` returns a `SimulationResult` (config, vehicles, generated count, `RunCounters`) instead of a dict | ASSUMPTIONS A-2026-09-19-15, made unattended (orchestrate loop) | none |
| D-2026-09-19-31 | 2026-09-19 | A lane-change request is used up by the lane change it makes: one decision, one lane change | Kerem (fix every bug; manuscript tex:335 "initiating a mandatory lane change") | none |
| D-2026-09-19-30 | 2026-09-19 | Driver split as built: `Vehicle(env, cfg, driver, origin_cell, destination)`, `HumanDriver`, `AutonomousDriver` registering with `AutonomousController`, one `VehicleFactory`; the seven `Vehicle` constants become `VehicleConfig`/`DriverConfig` fields with the same defaults; the link contract widened to the calls the vehicle already made | ASSUMPTIONS A-2026-09-19-12 to -14, made unattended (orchestrate loop) | none |
| D-2026-09-19-29 | 2026-09-19 | Scenario data (network, demand) belongs to the papers; `SimConfig` requires it and keeps only generic defaults | ASSUMPTIONS A-2026-09-19-8, accepted by Kerem | none |
| D-2026-09-19-28 | 2026-09-19 | `Incident`: cells blocked or slowed for a set time, then restored; listed in `SimConfig.incidents` | Kerem | none |
| D-2026-09-19-27 | 2026-09-19 | `OriginCell` and `DestinationCell` subclass `Cell`; transparent unless given a speed limit, which meters inflow or throttles outflow | Kerem | none |
| D-2026-09-19-26 | 2026-09-19 | Demand is veh/h per named (origin, destination) pair, one generator per pair; the network declares its origins and destinations, including one end per lane; S1 spreads end traffic over the four lane ends | Kerem | D-2026-09-19-11 (any-lane segment end, for S1) |
| D-2026-09-19-25 | 2026-09-19 | YAML configs: package defaults (vehicle, driver, controller) in `odca/configs/`, scenarios in each paper's `code/configs/`; `odca://`, file references and `_base_` overrides; `model` picks a lane-change family member | Kerem | none |
| D-2026-09-19-24 | 2026-09-19 | Driver split from Vehicle: `HumanDriver` (own process) and `AutonomousDriver` (called by `AutonomousController`); two-way link with a narrow contract; `HDV`/`AV` subclasses and the `vtype`/`dlc_enabled`-by-type switches go | Kerem | none |
| D-2026-09-19-23 | 2026-09-19 | One config per class: dataclass schemas plus `ConfigMixin`, all in `odca/params.py`; omegaconf validates once per run, frozen dataclasses inside; runtime objects (env, streams, cells) passed beside the config | Kerem | none |
| D-2026-09-19-22 | 2026-09-19 | MLC probability is per 5.2 cells driven, DLC probability per second (cooldown stays a refractory period); each evaluation converts over its exposure, q = 1-(1-p)^x | Kerem | none |
| D-2026-09-19-20 | 2026-09-19 | Measurement fixes: SimPy event count, all speed evaluations counted, lane changes per km over distance driven, space-mean speed in passage-time density | Kerem (fix every bug) | none |
| D-2026-09-19-19 | 2026-09-19 | AVs act at the controller rate, a blocked AV retries every controller_dt; vehicles placed at t=0 follow the AV share | Kerem (fix every bug) | none |
| D-2026-09-19-18 | 2026-09-19 | A lane change counts and starts its cooldown when it happens; the cooldown applies to discretionary changes only | Kerem (fix every bug) | none |
| D-2026-09-19-17 | 2026-09-19 | One exit path; a missed off-ramp retargets the next off-ramp or the segment end and is counted; a lateral request granted at patience expiry is released | Kerem (fix every bug) | none |
| D-2026-09-19-15 | 2026-09-19 | Delay is the per-cell sum of max(0, T_arr(c+1) - T_arr(c) - l/v_f) | Kerem (paper is the spec, paper-odca-des D-2026-09-19-16) | none |
| D-2026-09-19-14 | 2026-09-19 | Summary metrics cover every vehicle exiting in [warm-up, end], whenever it entered | Kerem (paper is the spec) | none |
| D-2026-09-19-13 | 2026-09-19 | The lane-change safety check rejects a target cell that has an occupant or a lock holder | Kerem (bugs first) | none |
| D-2026-09-19-12 | 2026-09-19 | Position changes only in `Vehicle._on_cell_change`, at arrival; the lock follows delayed release separately | Kerem (his `on_cell_change` design) | none |
| D-2026-09-19-11 | 2026-09-19 | Segment-end vehicles exit from their current lane | Kerem (paper is the spec) | none |
| D-2026-09-19-10 | 2026-09-19 | MIT license | inherited: paper-odca-des D-2026-09-19-10 | none |
| D-2026-09-19-9 | 2026-09-19 | Package scope: core, parameter types, analysis with the one CI function, NaSch, viewers (extra), experiment kit | inherited: paper-odca-des D-2026-09-19-9 | none |
| D-2026-09-19-8 | 2026-09-19 | Papers use this package as an editable path dependency; each paper's golden fingerprint is a test here | inherited: paper-odca-des D-2026-09-19-8 | none |
| D-2026-09-19-2 | 2026-09-19 | Parameter types live in `odca/params.py`; nothing in `odca` imports a paper's `config` | inherited: paper-odca-des D-2026-09-19-2 | none |
| D-2026-09-19-1 | 2026-09-19 | Package created from paper-odca-des `code/odca/`, history kept, under this doc set | Kerem (paper-odca-des D-2026-09-19-6 to -10) | none |
| D-2026-03-14-1 | 2026-03-14 | Randomness comes from one `SeedSequence` stream per source, shared by all vehicles, not one per vehicle | inherited: paper-odca-des D-2026-03-14-1 | none |

## D-2026-09-20-18: neighbour links are built once, and a reshaped road relinks
**What.** `Cell` keeps its eight neighbour links (next, previous, left, right and the four
diagonals) as plain slots, filled when the lanes are built. They are not recomputed on read. A road
whose shape changes after construction relinks explicitly: `Lane.make_periodic` for the ring road
used by the fundamental-diagram diagnostic, `Freeway.link_neighbours` otherwise. No script reaches
into `cell._next` any more.
**Evidence.** Kerem, 2026-09-20: "accept it". Every road in the papers is built once and then runs.
Recomputing the links on every read cost about 15 s per S1 run in the neighbour notify lists (code
review B4); after the change, quick-run wall time fell from 7.40 s to 7.17 s in S1 and from 10.34 s
to 8.90 s in S3, best of three on one machine, with the golden 24/24 exact and the ring-road FD
points byte-identical (D-2026-09-19-35). What it gives up: a road that gains or loses lanes during
a run would need either the links back on read or a call to `link_neighbours`. No paper does that;
the closest case, the ring road, is exactly why `make_periodic` exists.
**Replaces.** nothing.
**Cited by.** `odca/infrastructure/cell.py`, `odca/infrastructure/lane.py`,
`odca/infrastructure/freeway.py`.

## D-2026-09-20-17: a taken cell is a refused gap, not a separate failure
**What.** `HumanDriver.accepts_gap` refuses the target cell and counts a rejection in two cases,
under the same counter: the cell already holds a vehicle or its lock is held (`target.vehicle is
not None or target.is_occupied`), and the front or rear gap is smaller than the required one, which
grows from the jam spacing to the safety gap with the closing speed. The check is where the target
cell's own occupant and lock holder are seen at all: `find_leader` and `find_follower` start one
cell away.
**Evidence.** Kerem, 2026-09-20: "accept it". The same counting as the other safety failures: in
both cases the driver wanted the cell and did not take it. Its scale is now visible because the
counter was split today (D-2026-09-20-12): in the 24 golden runs every one of the 306,335 refusals
comes through this check and none through the patience timeout, since a cell refused here is never
requested. Whether the patience path is reachable at all is the open question, BACKLOG B12; this
decision fixes the counting, not that.
**Replaces.** nothing.
**Cited by.** `odca/entity/driver.py` (`accepts_gap`).

## D-2026-09-20-16: the viewers take a result, and the diagram splits by lane
**What.** `odca.viewer` takes one object: `TrafficVisualizer.from_result(result, ...)` for the
pygame playback, `animate_result(result, ...)` for the animation and `plot_trajectories(result,
...)` for the time-space diagram. The result already carries the network, the duration and the top
speed that the old 7 to 11 parameters repeated. In the diagram, a vehicle's consecutive records are
joined into one line while they stay in the same lane, instead of being split wherever more than
2 seconds passed between them, and each lane's lines are drawn as one collection.
**Evidence.** Kerem, 2026-09-20: "accept it". The lane test is exact where the gap test was a
guess: a vehicle that goes lane 1 to lane 2 and back used to be joined into one line by the gap
test, and a vehicle stopped for more than 2 seconds in one lane used to be cut in two. Nothing in
the manuscript depends on it: the viewers are not paper inputs (paper-odca-des D-2026-09-19-9), and
`fig:tsd` comes from `generate_paper_figures.py`. Checked headless when it landed
(D-2026-09-19-34): a pygame frame, an animation GIF and a diagram rendered from an S1 run,
`tests/test_viewer.py` covering the grid, the diagram and the time window at both ends. The old
`cell_range` option was not carried over (no caller), and a window-height bug that used a removed
argument was fixed in the move.
**Replaces.** nothing.
**Cited by.** `odca/viewer/animation.py`, `odca/viewer/playback.py`, `odca/viewer/snapshots.py`.

## D-2026-09-20-15: one experiment kit, one interval
**What.** `odca.experiment` holds what every paper does around a run: `RunRecord` (one per-seed
JSON, keys unchanged, plus the paper's extra keys), `run_once(label, config, measure, prepare)`
(build, prepare, run, time the run alone, measure), `write_run` and `read_runs` (strict JSON, the
same seed twice raises), and `aggregate`, `write_aggregate_csv`, `write_per_seed_csv` in today's
schema and six-decimal format. `odca.analysis.intervals.mean_ci95` is the package's only 95%
interval: a Student t table to 30 degrees of freedom, 1.96 above it. The paper's runners write only
per-seed JSONs; `aggregate_multiseed.py` is their one aggregator (paper-odca-des D-2026-09-19-3).
**Evidence.** Kerem, 2026-09-20: "accept it". Proved neutral when it landed: the five CSVs rebuilt
from the paper's 69 existing per-seed JSONs were byte-identical old against new, and the rewired
runners reproduced the golden stats and counters (D-2026-09-19-33). At the 20 seeds the paper uses,
the table is exact (19 degrees of freedom, t = 2.093). The 1.96 fallback only bites above 30 seeds,
where it narrows an interval slightly (at 40 degrees of freedom the true t is 2.021, about 3%
wider than 1.96); exact quantiles there would mean adding scipy.
**Replaces.** nothing.
**Cited by.** `odca/experiment/records.py`, `odca/experiment/tables.py`,
`odca/analysis/intervals.py`.

## D-2026-09-20-14: a run returns a typed result, not a dict
**What.** `Simulation.run()` returns `SimulationResult`, a frozen dataclass of four things: the
validated `config` it ran with, `vehicles` (those placed at t=0 first, then the generated ones, in
order), `num_generated` (generators only) and `counters`, a frozen `RunCounters`. What can be
derived is derived: `completed_vehicles`, `num_completed`, `num_active_at_end`. `config_yaml()`
writes the config back as YAML, so `Simulation(validate(SimConfig, path))` reruns it. The old
result dict is gone and every caller reads attributes; `asdict(counters)` keeps the per-seed JSON
keys as they were.
**Evidence.** Kerem, 2026-09-20: "accept it". Attribute names follow the old dict keys precisely so
the result files, the figures and the golden read the same, which is how the change was proved
neutral when it landed (D-2026-09-19-32, its golden 24/24 exact). The typed result is also what let
the viewers drop their 7 to 11 parameter lists (D-2026-09-19-34) and what the experiment kit's
`run_once` measures from (D-2026-09-19-33).
**Replaces.** nothing.
**Cited by.** `odca/simulation/result.py`, `odca/simulation/engine.py` (`Simulation.run`).

## D-2026-09-20-13: the autonomous names, `kind`, and one construction path
**What.** Three names as built. `AVController` is `AutonomousController`
(`odca/entity/controller.py`); an `AutonomousDriver` registers with it when constructed and is
decided for at the controller's `dt` rather than running a process of its own. A vehicle's kind is
the string its driver class carries, `vehicle.kind` in `"human"` or `"autonomous"`, replacing the
old `vtype` field. `VehicleFactory.build` is the one place a vehicle is built with its driver, used
by the generators and by `Simulation.seed_vehicles`. The configs keep the short pair, `av_vehicle`,
`av_driver`, `av_penetration`, `hdv_vehicle`, `hdv_driver`, and the manuscript keeps AV and HDV.
**Evidence.** Kerem, 2026-09-20: "accept all three". These are the names he used when the driver
split was designed (D-2026-09-19-24). Shape only: the split kept the golden 24/24 exact. `kind` is
read in five places in the package (pygame viewer, snapshots, the vehicle's string form) and in two
paper scripts, and `run_incident.py` writes it into every trajectory record, so the string is in the
incident result files. Noted and not acted on: the code names the same distinction three ways
(classes and `kind` long, config fields short, manuscript AV and HDV); renaming `av_penetration`
would touch every YAML, every result file and the quoted table columns.
**Replaces.** nothing.
**Cited by.** `odca/entity/controller.py`, `odca/entity/driver.py` (`kind`),
`odca/entity/vehicle.py` (`kind`), `odca/simulation/factory.py`.

## D-2026-09-20-12: the link as the vehicle uses it, and lane-change failures counted apart
**What.** Two halves, one decision. The link: a vehicle may ask its driver to `evaluate_speed()`
and `evaluate_direction()`, whether it `sees_blockage()`, whether it `accepts_gap(cell)`, and its
`merge_priority()` for the resource request, and it reads `tau`, `action_interval` and
`lc_patience`; the driver changes the vehicle only through `set_target_speed` and
`request_direction` (invariant 6). The counters: the vehicle counts moves (lane changes, patience
failures, missed exits), the driver counts decisions (slowdowns, car-following and speed
evaluations, gaps refused). `RunCounters.lc_failures` is no longer a stored field; it is two,
`lc_patience_failures` (from `Vehicle.count_lc_patience_failures`, renamed from
`count_lc_failures`) and `gap_rejections` (from the driver), with `lc_failures` kept as a derived
property for logging. Per-seed JSON therefore carries the two keys instead of the one.
**Evidence.** Kerem, 2026-09-20: "accept all three, and split lc_failures into two keys". Golden
re-recorded under this decision: 24 runs, every stat and every other counter identical, and
`lc_patience_failures + gap_rejections` equal to the old `lc_failures` in all 24, so the split
moved nothing. 86 tests pass. The split's first result: patience failures are 0 in all 24 golden
runs and all 306,335 failures are refused gaps, because `accepts_gap` refuses an occupied or locked
cell before the request is made, leaving the patience timeout reachable only in a same-instant race
(BACKLOG B12).
**Replaces.** nothing.
**Cited by.** `odca/simulation/result.py` (`RunCounters`), `odca/entity/vehicle.py`
(`count_lc_patience_failures`), `odca/entity/driver.py` (`count_gap_rejections`),
`odca/simulation/engine.py` (the run log).

## D-2026-09-20-11: the vehicle constants are config fields, split by who owns them
**What.** What used to be class constants on `Vehicle` are fields with the same values as defaults.
How a vehicle moves goes in `VehicleConfig`: `progressive_speed_threshold` 1.0 cell/s,
`traversal_dt` 0.25 s, `escape_speed` 1.0 cell/s. How a driver decides goes in `DriverConfig`:
`lc_patience` 3.0 s, `min_reeval_ratio` 0.5, `blockage_scan_mult` 3, `min_creep_speed`
0.1 cell/s, `slowdown_min_speed` 0.5 cell/s. The sub-step `traversal_dt` sits with the vehicle, not
as one run-wide value in `SimConfig` as the old HANDOVER had it, because it is how a vehicle crosses
a cell rather than a property of the run.
**Evidence.** Kerem, 2026-09-20: "accept it". Every default is the old constant, so the split moved
no number: the driver split it belongs to (N4, D-2026-09-19-24 and -30) kept the golden 24/24 exact.
**Replaces.** nothing.
**Cited by.** `odca/params.py` (`VehicleConfig`, `DriverConfig`), `odca/entity/vehicle.py`,
`odca/entity/driver.py`.

## D-2026-09-20-10: exposure starts at the first evaluation and the cooldown does not bank it
**What.** `HumanDriver._direction_exposure` returns (0, 0) the first time it is called and stores
the time and position at every call after that. Two consequences, both intended. A vehicle's first
direction evaluation after entering carries no exposure, so `probability_over` gives 0 for any
ordinary curve and only a forced change (p = 1, a blockage right ahead) can fire at that moment.
And an evaluation that happens while the discretionary cooldown is still running still resets the
clock, so the cooldown is a refractory period and the time inside it is not accumulated for the
first evaluation after it ends.
**Evidence.** Kerem, 2026-09-20: "accept both". Nothing has elapsed or been driven before the first
evaluation, so any exposure there would be invented. The cooldown is 10 s and an HDV evaluates at
least once a second, so about ten evaluations fall inside each one. With the reset, the first
evaluation after a cooldown carries roughly 1 s and gives q = 4.7% at zero speed advantage
(P = 0.047 per second); banked, it would carry 10 s and give q = 38.5%. Banking would therefore
raise the discretionary rate, which already stands at about 2.3 changes per vehicle-km in S1, 45%
of them away from the needed lane (`docs/lane-change-rate.md`, paper-odca-des AGENDA open decision).
Scale of the first-evaluation rule: once per vehicle, 107,694 completions over the 20 S1 seeds.
**Replaces.** nothing.
**Cited by.** `odca/entity/driver.py` (`_direction_exposure`, `evaluate_direction`),
`odca/models/lane_changing/rate.py` (`probability_over`).

## D-2026-09-20-9: the exposure references are one free-flow driver-second
**What.** `MLC_REFERENCE_CELLS = 5.2` in `odca/models/lane_changing/mandatory.py` is the distance
unit of the mandatory curve, and the discretionary curve's unit is one second
(`LogisticLaneChangeConfig`). Both are the exposure a free-flow driver accumulates in one second at
v_max = 5.2 cells/s, so `mlc_k`, `mlc_r0`, `dlc_k` and `dlc_v0` keep stating the chance that a
driver acts at one ordinary decision, and `probability_over` converts from there
(q = 1 - (1 - p)^x, D-2026-09-19-22).
**Evidence.** Kerem, 2026-09-20: "accept it and refer to this in the paper to justify why we
selected those parameters." The curves were fitted per decision of a free-flow driver, and a human
driver's action interval is 1.0 s, so a free-flow HDV evaluating once per second sees q = P and a
driver woken far more often in congestion gets the same exposure over the same distance rather than
more attempts. The reference is not a free knob: a reference c times longer leaves behaviour
unchanged only under 1 - P' = (1 - P)^c. paper-odca-des D-2026-09-20-8 puts this in the manuscript.
**Replaces.** nothing.
**Cited by.** `odca/models/lane_changing/mandatory.py` (`MLC_REFERENCE_CELLS`),
`odca/models/lane_changing/rate.py` (`probability_over`), `odca/entity/driver.py`
(`mlc_exposure`), `odca/params.py` (`LogisticLaneChangeConfig`).

## D-2026-09-20-8: the wrong end lane is a missed exit, not a second chance
**What.** At the last cell, a vehicle whose destination names a lane it is not in exits anyway and
`count_missed_exits` goes up by one (`Vehicle._movement_process`). It is the same counter a missed
off-ramp increments, where the vehicle is retargeted to the next off-ramp downstream or to the
segment end (`_retarget_missed_exit`). No vehicle is held on the road, sent around, or dropped from
the results: it leaves, its trip is measured, and the run reports the failure through the counter.
**Evidence.** Kerem, 2026-09-20: "accept it". The dissertation reports these as exit failures
(4.3, "Success Flag"), and the road offers nothing downstream to a vehicle in the last cell. Scale
in the current S1-S4 results, 20 seeds each: missed exits are 16.4% of completions in S1 (17,668 of
107,694), 10.0% in S2, 6.7% in S3 and 5.4% in S4 (6,873 of 128,024), falling as AV share rises and
lane changing gets easier. The counter bundles both kinds, a missed off-ramp and a wrong end lane,
so those percentages are not this rule alone; the per-seed files store only the total.
**Replaces.** nothing.
**Cited by.** `odca/entity/vehicle.py` (`_movement_process`, `_passed_exit`,
`_retarget_missed_exit`), `odca/simulation/result.py` (`RunCounters.missed_exits`).

## D-2026-09-20-7: the any-lane `end` stays for the lane-drop runs
**What.** `DestinationConfig.lane` None means any lane, and `NetworkConfig.corridor` publishes it
as `end` beside `end_lane_<n>`. A vehicle bound for `end` leaves at the downstream edge of the last
cell from whatever lane it is in, so its route asks for no mandatory lane change. The paper's
bottleneck (3 lanes, 600 cells, lane 3 closed from cell 300 to the end, 3,600 veh/h at 1,200 per
lane), incident (4 lanes, 4,500 veh/h at 1,125 per lane, two lanes closed for a while) and
scalability runs use it for their demand and for the vehicles placed at t=0. S1 to S4 use the four
per-lane ends instead (D-2026-09-19-26), which is where the mandatory lane changes come from.
**Evidence.** Kerem, 2026-09-20: "accept it". The bottleneck is why the destination exists: with
per-lane ends, a third of its demand, 1,200 veh/h, would be bound for the end of a lane that is
closed from cell 300 onwards, so those vehicles could never exit. The rejected alternative, per-lane
ends everywhere, would also have moved every bottleneck, incident and scalability number the
manuscript quotes (bottleneck throughput 2,501 veh/h at 0% AV, 3,602 at 70%), which means a rerun
and a restatement, not an edit.
**Replaces.** nothing.
**Cited by.** `odca/params.py` (`DestinationConfig`, `NetworkConfig.corridor`),
`odca/infrastructure/freeway.py` (destination cells per lane), `odca/entity/vehicle.py`
(`destination_lane` None); paper-odca-des `code/run_bottleneck.py`, `run_incident.py`,
`run_scalability.py`.

## D-2026-09-20-6: origins and destinations keep their readable names
**What.** A network names its places in words: origins `mainline_lane_<n>` and `onramp_<k>`,
destinations `offramp_<k>`, `end_lane_<n>` and `end` (`NetworkConfig`, `NetworkConfig.corridor`,
and every scenario YAML a paper keeps). The dissertation's letters (lanes 1 to 4, O1, off-ramps
A to D, F1) stay in the dissertation; a paper that wants to print them maps them in its own text,
and no legend file is added.
**Evidence.** Kerem, 2026-09-20: "accept it, keep the words". The names are dictionary keys and
nothing reads meaning from them, so no number moves and no golden is touched. The manuscript
already names places in words rather than letters: Section 5.1 gives "two on-ramps (lane 1 at
cells 100 and 400), three off-ramps (lane 1 at cells 300, 550 and 750) and one exit per lane at
the segment end", and the geometry figure caption is written the same way. The rejected
alternative, letters in the YAML, would also have meant regenerating the 124 per-seed JSON files
in paper-odca-des, which carry these keys.
**Replaces.** nothing.
**Cited by.** `odca/params.py` (`NetworkConfig`, `NetworkConfig.corridor`); paper-odca-des
`code/configs/network_s1.yaml`, `demand_s1.yaml`, `demo_corridor.yaml`.

## D-2026-09-20-5: report what a vehicle takes from the road, not only what the road does to it

**What.** A vehicle's position is still the cell label, changing at T_arr, and the lock still follows
the delayed release, T_rel(c) = T_acq(c+1) + tau. What changes is that the second half is now
reported, not only modelled. Every `TrajectoryRecord` carries `acquired` (T_acq) beside `time`
(T_arr), the two stamps the protocol already defines, so `summary_statistics` reads three new
numbers off the trajectory with no state kept on the vehicle: `avg_cells_held` (the mean number of
cells a vehicle holds while it drives), `avg_origin_wait` (the time between the generator releasing
it and it getting onto the road) and `num_never_entered` (vehicles that never got on at all, counted
over every vehicle rather than the completed ones). `Vehicle.time_created` is the one new field, the
stamp a trajectory cannot carry because it predates the trip.

**Evidence.** Kerem, 2026-09-20: "We should report both together, a vehicle occupying multiple cells
means those cells can't be seized by others", and, on how to compute it, "TBH, creating everything
from trajectories should be fine." Measured on a 1,200 s run, seed 42: in S1 a vehicle is labelled
in one cell and holds 5.23 of them, in S4 4.89; S1's mean origin wait is 18.9 s with 117 of 2,330
vehicles never admitted, S4's is 0.7 s with none. The trajectory reading was checked against exact
per-cell bookkeeping inside the vehicle and agrees to 0.15%, the remainder being the endpoint cells
(a metered origin, a throttled exit), which are not road cells and are not in the trajectory. The
bookkeeping was then deleted. Golden re-recorded: three keys added, zero values moved, across all
24 runs; 86/86 tests.

⚠️ My reading, not Kerem's words: the manuscript's tables carry none of these numbers yet, because
the per-seed result files were written before the metrics existed. They arrive with the next run
that regenerates those files, which is also what BACKLOG B10 was waiting for.

**Replaces.** nothing; it closes BACKLOG B10, parked this morning.
**Cited by.** `odca/entity/vehicle.py` (`TrajectoryRecord`, `_acquired_at`, `time_created`),
`odca/analysis/metrics.py` (`cells_locked`, `summary_statistics`).

## D-2026-09-20-4: a speed limit takes effect on the cell that posts it

**What.** A vehicle crosses a cell at the speed its driver last chose. When it arrives in a cell
whose speed limit differs from the one it left, `Vehicle._on_cell_change` now calls
`driver.evaluate_speed()` before the trajectory record is written and before the crossing begins, so
the new limit governs that cell. The asynchronous route that used to serve this, `Driver.react_now`
and the `simpy.Interrupt` branch in `HumanDriver._run`, is removed: it woke the driver after the
next crossing had already started, which is the bug, and nothing else called it.

**Evidence.** Kerem, 2026-09-20: "Fix the thing work-zone test revealede. Fix B11 too." Both name
the same finding, from `tests/test_delay.py`. Before: a lone vehicle through a 20-cell work zone
posted at 1.3 cells/s crossed the first slow cell at 5.2 (0.192 s) and the first fast cell after the
zone at 1.3 (0.769 s), so it gained 0.577 s entering and lost 0.577 s leaving, and per-cell clipping
reported the loss as 0.577 s of delay that no other vehicle caused. After: every cell is crossed at
what it posts (1/5.2 at cells 19 and 40, 1/1.3 at cells 20 and 39) and the vehicle's delay is 0.000 s
while its trip is 11.5 s longer than without the zone. Neutral for the papers: no scenario here posts
a limit that varies along the road, so the re-evaluation never fires. Golden 24/24 exact, 86/86 tests.

**Replaces.** nothing; it closes BACKLOG B11, parked the same day.
**Cited by.** `odca/entity/vehicle.py` (`_on_cell_change`), `tests/test_delay.py`.

## D-2026-09-20-3: free flow is per vehicle and per cell

**What.** Three quantities, kept apart: `v_max(n)`, what vehicle n can do; `v_lim(c)`, what cell c
posts; and the free-flow speed `v_f(n, c) = min(v_max(n), v_lim(c))`, what n would hold on c with
no other vehicle in the way. `Vehicle.effective_v_max()` is that quantity, every trajectory record
carries it as `v_free`, and `analysis.metrics.delay` subtracts `l / v_f(n, c)` cell by cell instead
of `l / v_max(n)` throughout. Delay therefore measures what other traffic costs a vehicle: a work
zone changes the free-flow travel time, not the delay. The manuscript uses the same three symbols
(Eq. free_flow_speed and Eq. delay).

**Evidence.** Kerem, 2026-09-20: "I was using v_f and v_max interchangable, but it might be wise to
use one as the speed limit which might be less than v_f for workzone. v_f by the traffic flow
theory definition would stay as the unlimited free flow speed", and "Confirmed on both code and
text change." The readings differ on one unimpeded vehicle crossing a 50-cell work zone posted at
2.6 cells/s on a 6 km segment: trip 163.46 s, old reading 9.62 s of delay, new reading 0.00 s.
They do not differ on anything this paper runs: every cell of S1 to S4, the bottleneck, the
incident and the scalability runs posts 5.2 cells/s and both vehicle types have `v_max` 5.2, so
`min()` changes nothing. Proof: 83/83 tests pass, golden 24/24 exact. New `tests/test_delay.py`:
a work zone lengthens the trip by more than 10 s and adds under 1.2 s of delay, while a leader in
the same zone still causes delay.

⚠️ My reading, not Kerem's words: the test's residual is not noise. A vehicle crosses a cell at the
speed it chose on arriving in the previous one, so a limit change takes effect one cell late at both
ends of a zone. Entering, it gains 0.577 s; leaving, it loses the same, which per-cell clipping
records as delay. Parked as BACKLOG B11; it changes no number in this paper because no scenario
here posts a limit that varies along the road.

**Replaces.** nothing.
**Cited by.** `odca/entity/vehicle.py` (`TrajectoryRecord.v_free`, `effective_v_max`),
`odca/analysis/metrics.py` (`delay`), `tests/test_delay.py`.

## D-2026-09-20-2: the clock starts when the vehicle gets on the road
**What.** `Vehicle.start` sets `time_entered` only after the origin cell is seized, so travel time
and delay cover the road and nothing else. A vehicle that the generator has released but that
cannot get on yet waits invisibly: no metric counts that wait, and a vehicle that never gets on
before the run ends appears in no result file. Kerem asked for the wait to be reported beside
travel time rather than folded into it; that reporting is deferred because no run file carries the
creation time it needs (BACKLOG B10).
**Evidence.** Kerem, 2026-09-20: "report it separately, third reading unless you have to rerun
everything. o.w., accept and go on." Rerunning everything is what it would take: creation time is
not stored on the vehicle, so the probe that measured this had to patch `VehicleFactory.build`, and
adding the metric changes `Vehicle`, `summary_statistics` and the per-seed JSON, which means
regenerating all 124 run files. Measured on a 1,200 s S1 probe: 2,330 vehicles created, 117 never
got on the road, mean wait 21.9 s (median 10.0, 90th percentile 64.7, maximum 105.4), half waited
over 10 s; mean travel time 243.6 s as reported against 262.5 s with the wait added, a difference
of 7.8%. Manuscript tex:974 defines travel time "from entry to exit", which is what the code does.
**Replaces.** nothing.
**Cited by.** `odca/entity/vehicle.py` (`Vehicle.start`).

## D-2026-09-20-1: the vehicles placed at t=0 leave from any lane
**What.** `Simulation.seed_vehicles` gives every placed vehicle the segment-end destination with no lane requirement, the same treatment generated segment-end traffic gets (D-2026-09-19-11). Birth does not change the rule: a vehicle bound for the end of the road leaves from the lane it is in, whether it entered through an origin or started the run on the road.
**Evidence.** Kerem, 2026-09-20: "accepted". Manuscript tex:874 states the rule for segment-end vehicles as a class. The scenarios it touches seed few vehicles: the bottleneck 72 against 1,169 completions in seed 1, the incident 80 against 4,025, so under 6% either way; the readings differ most in the bottleneck, where the alternative would commit a third of the seeded vehicles to the lane that closes.
**Replaces.** nothing.
**Cited by.** `odca/simulation/engine.py` (`seed_vehicles`).

## D-2026-09-19-35: neutral speed-ups from the code review
**What.** `Cell` keeps its eight neighbour links (`next`, `previous`, `left`, `right`, four diagonals) and its occupant as plain slots, set when the lanes are built (`Lane`, `Freeway.link_neighbours`); a road whose shape changes after that relinks (`Lane.make_periodic` for a ring road). `Lane.blocked_count` is kept by the `Cell.blocked` setter, so `find_blockage` answers at once on a lane with no closed cell (S1 to S4 have none). `AutonomousController.active_drivers()` drops drivers whose vehicle has left, in registration order. `metrics.cell_speeds` and `RNGRegistry.get` (unused) are gone.
**Evidence.** Code review 2026-09-19 (`docs/code-review-2026-09-19.md`): top-10 item 9, B1, B4, B5, A24 (A27, typing `Cell` against `Vehicle`, is left out: `infrastructure` never imports `entity`). Golden 24/24 exact; ring-road FD points from the paper's `diagnose_fd_capacity.py` byte-identical against main; `tests/test_infrastructure.py`. Wall time, 300 s quick run, best of 3, same machine: S1 7.40 to 7.17 s, S3 (50% AV) 10.34 to 8.90 s. Made unattended; the review's non-neutral items (B6, B7, B8, B13, C1) are BACKLOG B7 to B9.
**Replaces.** nothing.
**Cited by.** `odca/infrastructure/cell.py`, `lane.py`, `freeway.py`, `odca/entity/controller.py`.

## D-2026-09-19-34: viewers in the package
**What.** `odca.viewer.snapshots` (the one `VehicleSnapshot`, which both paper viewers had copied, and `reconstruct_grid`), `odca.viewer.animation` (`animate_result`, `plot_trajectories`) and `odca.viewer.playback` (`TrafficVisualizer.from_result`), behind the `[viewer]` extra. Each takes a `SimulationResult`, so the 7 to 11 parameter lists go. The paper's `visualize.py` and `animate.py` keep only their command-line options and the S1 run.
**Evidence.** HANDOVER N7, paper-odca-des D-2026-09-19-9. Headless smoke run: a pygame frame, an animation GIF and a time-space diagram rendered from an S1 run; `tests/test_viewer.py` (grid, diagram, time window on both ends of a segment, a headless pygame frame). The `cell_range` option of the old diagram is not carried over (no caller). The window height used the removed `num_lanes` argument; fixed in the move. Signatures chosen unattended: ASSUMPTIONS A-2026-09-19-17.
**Replaces.** nothing.
**Cited by.** `odca/viewer/`.

## D-2026-09-19-33: the experiment kit
**What.** `odca.experiment`: `RunRecord` (one run: label, AV share, seed, the two action intervals, stats, counters, and the paper's extra keys, written as today's per-seed JSON), `run_once(label, config, measure, prepare)` (build, prepare, run, measure; `wall_time_s` times the run alone, where `run_experiments.py` used to include building the simulation), `write_run` and `read_runs` (strict JSON through `numpy_default`; the same run twice raises), `aggregate`, `write_aggregate_csv` and `write_per_seed_csv` (today's schema and six-decimal format). `odca.analysis.intervals.mean_ci95` is the one 95% interval: Student t table to 30 degrees of freedom, 1.96 above, as the paper's copies did. The paper's runners write only per-seed JSONs; `aggregate_multiseed.py` is their only aggregator (paper-odca-des D-2026-09-19-3).
**Evidence.** HANDOVER N6, paper-odca-des D-2026-09-19-9. The five CSVs rebuilt from the paper's 69 existing per-seed JSONs are byte-identical old against new; the rewired runners reproduce the golden stats and counters (S1, S4 and the four bottleneck runs, seed 1, checked by hand); `run_once` with its prepare hook is tested in `tests/test_experiment.py`. Review: extra keys may no longer overwrite a record's own keys. Shape chosen unattended: ASSUMPTIONS A-2026-09-19-16.
**Replaces.** nothing.
**Cited by.** `odca/experiment/`, `odca/analysis/intervals.py`.

## D-2026-09-19-32: a typed run result
**What.** `Simulation.run()` returns `SimulationResult(config, vehicles, num_generated, counters)` from `odca/simulation/result.py`; `completed_vehicles`, `num_completed` and `num_active_at_end` are derived properties, `config_yaml()` writes the validated config so a run can be repeated from its result. `RunCounters` is a frozen dataclass with the eight counters under their old key names, so `asdict(result.counters)` writes the same JSON as before. The result dict is gone; the golden scenarios and every paper runner read attributes.
**Evidence.** HANDOVER N5. Golden 24/24 exact; `test_result_carries_the_config_it_ran_with` round-trips the config through `config_yaml()`; the paper's S1 quick run reproduces the golden values (1.81 lane changes per km, 22.75 s delay, 3080 veh/h). Field names made unattended: ASSUMPTIONS A-2026-09-19-15.
**Replaces.** nothing.
**Cited by.** `odca/simulation/result.py`, `odca/simulation/engine.py` (`Simulation.run`).

## D-2026-09-19-31: one lane-change request, one lane change
**What.** After a lateral move, `Vehicle._advance_to` sets the requested direction back to forward. Before, the request stayed until the driver decided again (1 s for a human, about 5 cells at free flow), so one MLC or DLC decision could make several lane changes in a row, each skipping the cooldown and gap re-evaluation by the driver.
**Evidence.** Found while plotting the demo corridor (paper-odca-des `code/demo_trajectories.py`): 4.4 lane changes per vehicle-km there and 3.9 in S1, half of them away from the lane the vehicle needed. `tests/test_drivers.py::test_one_request_makes_one_lane_change` made 2 changes from one request before the fix. Golden re-recorded: S1 seed 1 lane changes per km 4.98 to 1.81, delay 30.6 to 22.8 s, throughput 2880 to 3080 veh/h, missed exits 57 to 38; S4 seed 1 lane changes per km 2.09 to 0.65; bottleneck runs move less and not all one way: with no AVs, delay rises on two of three seeds (seed 1 80.7 to 84.4 s, seed 3 67.5 to 69.9 s) and falls on seed 2 (69.1 to 66.7 s), within seed spread; a vehicle leaving the closed lane now needs a new decision per lane change instead of riding one request. Full table in STATUS 2026-09-19 (N4b).
**Replaces.** nothing.
**Cited by.** `odca/entity/vehicle.py` (`_advance_to`).

## D-2026-09-19-30: driver split as built
**What.** `Vehicle` keeps the physical side (position, lock, movement, exit, trajectory, move counters) and takes `(env, cfg, driver, origin_cell, destination)`. `Driver` in `odca/entity/driver.py` holds every decision and its state; `HumanDriver` decides in its own process, `AutonomousDriver` registers with `AutonomousController` (`odca/entity/controller.py`, renamed from `AVController`) and acts at its `dt`. `VehicleFactory` (`odca/simulation/factory.py`) builds each vehicle with its driver for the generators and for the vehicles placed at t=0. `HDV`, `AV`, `VehicleType` and `config_kwargs` are gone; reporting reads `vehicle.kind`. The seven class constants become config fields with today's values as defaults: `progressive_speed_threshold`, `traversal_dt`, `escape_speed` in `VehicleConfig`; `lc_patience`, `min_reeval_ratio`, `blockage_scan_mult`, `min_creep_speed`, `slowdown_min_speed` in `DriverConfig`. The vehicle-to-driver calls are the ones it already made: wake, react now (speed-limit change), gap and blockage judgement, and reads of tau, action interval, patience and merge priority.
**Evidence.** Golden fingerprint 24/24 exact; the paper's demand sweep, ring-road FD and car-following scripts give byte-identical output before and after. Made unattended in the orchestrate loop; the calls are ASSUMPTIONS A-2026-09-19-12 to -14, open for Kerem.
**Replaces.** nothing (implements D-2026-09-19-24).
**Cited by.** `odca/entity/vehicle.py`, `odca/entity/driver.py`, `odca/entity/controller.py`, `odca/simulation/factory.py`, `ARCHITECTURE.md` invariant 6.

## D-2026-09-19-29: scenario data belongs to the papers
**What.** The network and demand of a scenario live in the paper's YAML; `SimConfig` requires them
and has defaults only for generic settings (duration, warm-up, seed, controller rate).
**Evidence.** ASSUMPTIONS A-2026-09-19-8, Kerem 2026-09-19: "Assumption OK".
**Replaces.** nothing.
**Cited by.** `odca/params.py` (`SimConfig`), paper-odca-des `code/configs/`.

## D-2026-09-19-28: incidents
**What.** `IncidentConfig` (start, duration, a lane and cell range or an origin or destination
name, and a speed limit, None meaning blocked) in `SimConfig.incidents`; `Incident.run` saves
each cell's state, applies the change, waits the duration and restores it. An origin or
destination can be throttled, not blocked. `odca/infrastructure/incident.py`.
**Evidence.** Kerem, 2026-09-19: "Let's also add Incident or Event Classes which can adjust the
outflow capacity of certain cells or compeletely block them. Since Event is very simpyish, I
would go for the wording Incident. It will just change the state of the cell(s) for a given
amount of time and resolve." paper-odca-des `run_incident.py` now uses it.
**Replaces.** nothing.
**Cited by.** `odca/infrastructure/incident.py`, `tests/test_incidents_and_endpoints.py`.

## D-2026-09-19-27: origin and destination cells
**What.** `OriginCell` and `DestinationCell` subclass `Cell` (`EndpointCell`). An origin has one
origin cell joined to its road cell; a destination has one destination cell per lane it is left
from. Without a speed limit an endpoint is transparent (no time, no lock), so trips run as
before; with one, a vehicle passes it at the limit and holds it tau more, capping flow at
3600 / (tau + 1 / limit) veh/h per lane. `Origin.set_speed_limit`, `Destination.set_speed_limit`.
**Evidence.** Kerem, 2026-09-19: "it would be a better way to model it since we can adjust a
cell's outflow at anytime by its v_max to create artificial bottlenecks at offramps or mainline
ends"; default answered "Transparent: same timing as today". Golden exact against the recording
before the change.
**Replaces.** nothing.
**Cited by.** `odca/infrastructure/cell.py`, `freeway.py`, `Vehicle.start`, `Vehicle._exit`.

## D-2026-09-19-26: named origins and destinations, OD demand in veh/h
**What.** `NetworkConfig` declares `origins` (lane, cell) and `destinations` (cell, lane, None
for any lane) by name; the freeway builds them and refuses unknown names or places off the road.
`SimConfig.demand` gives veh/h per (origin, destination) pair; one generator per pair. A vehicle
reaching the last cell outside its end lane leaves and counts as a missed exit. S1 keeps its
network and per-origin totals; the end-of-segment share of each origin is spread evenly over
`end_lane_1..4`. `NetworkConfig.corridor` gives a ramp-free segment with every lane end and
`end` (any lane).
**Evidence.** Kerem, 2026-09-19: "the way we define demand is stupid ... We should first define
destinations"; "I am leaning towards 2 because I want to introduce some lane changing by starting
from lane 1 and end the stretch at lane 4"; S1 answered "Keep 6 km S1, spread end lanes".
Dissertation 4.1: "The downstream ends of the lanes are destinations A, B, C and D"; 4.1.1: "For
each OD flow, a fixed demand rate is specified, denoted as λ vehicles per hour". Golden: every
run moved; seed 1 S1 lane changes per km 2.09 -> 4.98, delay 29.1 -> 30.6 s.
**Replaces.** D-2026-09-19-11 for S1-S4 (their segment end was any lane).
**Cited by.** `Freeway`, `NetworkConfig`, `Simulation._od_pairs`, `VehicleGenerator`.
⚠️ Every call under this decision is now Kerem's: the readable names since D-2026-09-20-6, the
any-lane `end` since D-2026-09-20-7, the wrong end lane counted as a missed exit since
D-2026-09-20-8.

## D-2026-09-19-25: YAML configs, package defaults and paper scenarios
**What.** `odca/configs/` ships the published vehicle, driver and controller YAML; a paper keeps
its network, demand and run YAML in `code/configs/`. A string where a config, list or table
belongs names a file (relative, or `odca://` for the package); `_base_` plus keys starts from a
file and overrides at any depth; `model:` picks the member of a config family (lane change).
**Evidence.** Kerem, 2026-09-19: "I want YAML."; "We can have separate config.yaml files in
different places. For example a config folder inside odca"; placement answered "Defaults in
odca, scenarios in paper"; "scenario can override the defaults right?".
**Replaces.** nothing.
**Cited by.** `odca/params.py` (`validate`, `ConfigFamily`), `odca/configs/`.

## D-2026-09-19-24: driver split from vehicle
**What.** `Vehicle` keeps only the physical process common to every vehicle: position label,
cell lock with delayed release, forward and lateral movement, exit, trajectory. The decisions move
to `Driver` in `odca/entity/driver.py`: target speed, direction, lane-change curves (through
`models/`), gap acceptance, and the decision state (`_direction_exposure`, last evaluation time and
position). `HumanDriver` runs its own SimPy process (action interval, wake-ups, random slowdown);
`AutonomousDriver` has no process, the `AutonomousController` calls it every controller_dt.
Both sides hold a reference (`vehicle.driver`, `driver.vehicle`) under one contract: the driver
reads vehicle state and reaches neighbours through cells, and changes the vehicle only through a
small command set; the vehicle calls the driver only to wake it and to read tau (the release stays
in `Vehicle`, the part the paper describes). The class constants become config fields: the
driver's (`_LC_PATIENCE`, `_ESCAPE_SPEED`, `_MIN_REEVAL_RATIO`, `_PROGRESSIVE_SPEED_THRESHOLD`,
`_BLOCKAGE_SCAN_MULT`, `_MIN_CREEP_SPEED`) in the driver configs, `_TRAVERSAL_DT` in `SimConfig`.
`HDV` and `AV` classes go; a vehicle's type is its driver's class.
**Evidence.** Kerem, 2026-09-19: "So each Vehicle will have a controller, HDVs will be controlled
by HumanDriver, AVs will be controlled by AutonomousDriver, which collectively get controlled by
AutonomousController"; "Only common Vehicular movement processes stay in the Vehicle class";
"agree with your two way link and the limits." `vehicle.py` is 894 lines with 40 methods.
**Replaces.** nothing.
**Cited by.** HANDOVER N4 (planned); ARCHITECTURE Boundaries, Core types, invariant 6.
⚠️ Mine, not Kerem's: one `AutonomousController` per run as the default; controllers per road
segment are BACKLOG B5, a model feature (roadside units), not a speed-up, since SimPy runs on one
thread and the work is one decision per AV per tick however it is split.

## D-2026-09-19-23: one config per class, ConfigMixin, schemas in params.py
**What.** Each configurable class declares `Config = <schema>` and takes one `cfg` in `__init__`,
plus the runtime objects it needs (env, RNG streams, cells, its vehicle), never inside the config.
All schemas are plain dataclasses in `odca/params.py`, composed by `SimConfig`. `ConfigMixin`
(also there) gives `from_config` (dict, YAML or dataclass in; omegaconf `structured` + `merge`
validates types and unknown keys; `to_object` out) and `save_config` (the resolved config written
into each run's result). omegaconf is used only at the run boundary: inside the simulation every
config is a frozen dataclass with slots, so no attribute access goes through omegaconf.
**Evidence.** Kerem, 2026-09-19: "You may also want to use omegaconf for class initializations.
Looks like inits have too many arguments"; "Public pattern"; "ConfigMixin could be a class to
inherit"; schema home answered "All in odca/params.py". `Vehicle.__init__` has 24 parameters,
`VehicleGenerator` 17.
**Replaces.** nothing (narrows inherited D-2026-09-19-2: same module, now with the mixin).
**Cited by.** HANDOVER N2 (planned).

## D-2026-09-19-22: lane-change probability per distance (MLC) and per second (DLC)
**What.** The logistic MLC curve gives a probability per 5.2 cells driven, the DLC curve a
probability per second. Each evaluation uses q = 1 - (1 - p)^x, x = cells driven since the last
direction evaluation / 5.2 (MLC) or seconds since it (DLC); p = 1 stays 1, x = 0 gives 0. The 10 s
DLC cooldown stays as a refractory period. `odca/models/lane_changing/rate.py`.
**Evidence.** Kerem, 2026-09-19: "MLC per distance, DLC per second (Recommended)". Analysis: with
p per evaluation, 50% of vehicles have attempted the MLC at remaining-distance ratio 0.85 for AVs
(10 Hz) against 0.60 for free-flow HDVs; per second, congested HDVs still reach 0.78; per distance
all cases give 0.60 (docs/lane-change-rate.md). Quick golden re-recorded: all 24 runs moved.
**Replaces.** nothing (the per-evaluation reading was never decided).
**Cited by.** `odca/models/lane_changing/rate.py`, `Vehicle._direction_exposure`, `mandatory.MLC_REFERENCE_CELLS`.

## D-2026-09-19-20: measurement fixes
**What.** `Simulation` runs on `CountingEnvironment`, and `counters["simpy_events"]` is the number of SimPy events processed: the paper's "events" (tex:1172, seize, release, driver and wait events), where the old scalability "total events" summed four behaviour counters. `counters["speed_evaluations"]` counts every speed evaluation (free flow included) next to `cf_evaluations`. `avg_lc_per_km` divides by the distance actually driven (first to last recorded cell). `passage_time_flow` uses the harmonic mean of spot speeds (space-mean speed), so k = q / v holds.
**Evidence.** Opus principal-engineer review 2026-09-19 (`docs/code-review-2026-09-19.md`); Kerem, 2026-09-19: "Fix every bug." Golden S1 seed 1 (300 s): 2,253,912 SimPy events against about 57,000 under the old counter sum; the paper's event figures (tex:1157, tex:1183 table, tex:1197) are restated at paper N11.
**Replaces.** Nothing.
**Cited by.** `odca/simulation/engine.py` `CountingEnvironment`, `_collect_results`; `odca/analysis/metrics.py` `summary_statistics`, `passage_time_flow`.

## D-2026-09-19-19: AV timing and the initial vehicles
**What.** `AVController.register` sets the AV's `action_interval` to `controller_dt`: an AV decides at the controller rate (tex:398), so a blocked AV retries its move every 0.1 s instead of 0.5 s. `Simulation.seed_vehicles` draws each initial vehicle's type from the AV share, with its own RNG stream spawned last.
**Evidence.** Opus principal-engineer review 2026-09-19 (`docs/code-review-2026-09-19.md`); Kerem, 2026-09-19: "Fix every bug." (A19, A20). Before: an AV at standstill lagged up to 0.5 s behind a 10 Hz controller; BN_70av started from an all-HDV road.
**Replaces.** Nothing.
**Cited by.** `odca/entity/controller.py` `register` (the file was `av_controller.py` until
D-2026-09-19-30); `odca/simulation/engine.py` `seed_vehicles`.

## D-2026-09-19-18: lane-change counting and cooldown
**What.** `count_lane_changes` and `last_lc_time` change when a lateral move is granted, not when it is attempted (a patience expiry no longer counts or starts a cooldown). The cooldown gates discretionary lane changes only; mandatory ones (exit lane, blockage) are never delayed by it.
**Evidence.** Opus principal-engineer review 2026-09-19 (`docs/code-review-2026-09-19.md`); Kerem, 2026-09-19: "Fix every bug." (A5, A6); manuscript tex:352 places the cooldown in the DLC description.
**Replaces.** Nothing.
**Cited by.** `odca/entity/vehicle.py` `_advance_to`, `_evaluate_direction`.

## D-2026-09-19-17: exits and the lateral-request race
**What.** The movement loop is the only exit path (the end of the road exits there, no second process). A vehicle that passes its off-ramp without reaching lane 1 takes the next off-ramp downstream, or the segment end from any lane, and `counters["missed_exits"]` counts it; its remaining-distance ratio restarts from where it missed. A lateral request granted in the instant its patience expires is released instead of holding the cell forever.
**Evidence.** Opus principal-engineer review 2026-09-19 (`docs/code-review-2026-09-19.md`); Kerem, 2026-09-19: "Fix every bug." (A7, A8, A10). Before: a missed vehicle exited at the first later cell where it reached lane 1, ramp or not, uncounted. Golden: 6 to 8 missed exits per quick S run.
**Replaces.** Nothing.
**Cited by.** `odca/entity/vehicle.py` `_movement_process`, `_retarget_missed_exit`, `_advance_to`.

## D-2026-09-19-15: per-cell delay
**What.** `metrics.delay` sums, over consecutive trajectory arrivals, max(0, T_arr(c+1) - T_arr(c) - 1/v_max) (cells, s). It replaces total travel time minus distance over v_max, which also counted extra cells driven past a missed off-ramp as delay.
**Evidence.** Manuscript tex:975 defines this formula; Kerem, 2026-09-19: paper is the spec. Found by the session (not in the review). Golden: delay moves on 24/24 runs, S1 seed 1 26.9 to 25.6 s.
**Replaces.** Nothing.
**Cited by.** `odca/analysis/metrics.py` `delay`.

## D-2026-09-19-14: measurement window by exit time
**What.** `summary_statistics` counts every vehicle whose exit time lies in [warmup, sim_duration]; travel time, delay and lane-change rate average over the same vehicles. It replaces "entered after warm-up", which dropped vehicles already on the road at warm-up and understated throughput.
**Evidence.** Manuscript tex:973 ("total vehicles exiting the network during the measurement period"); Kerem: paper is the spec. Opus principal-engineer review 2026-09-19 (`docs/code-review-2026-09-19.md`), checked by the session against the code and the manuscript. Golden (quick, 300 s): throughput up 25 to 35%, e.g. S1 seed 1 2,440 to 3,240 veh/h; smaller in full-length runs.
**Replaces.** Nothing.
**Cited by.** `odca/analysis/metrics.py` `summary_statistics`.

## D-2026-09-19-13: target cell occupancy in the lane-change safety check
**What.** `_check_lc_safety` fails when the target cell has a position label or a lock holder; `find_leader` and `find_follower` start one cell away and never saw it.
**Evidence.** Opus principal-engineer review 2026-09-19 (`docs/code-review-2026-09-19.md`), checked by the session against the code and the manuscript. Kerem: fix bugs first. Golden: S1 seed 1 lane changes per km 3.57 to 2.08.
**Replaces.** Nothing.
**Cited by.** `odca/entity/vehicle.py` `_check_lc_safety`.

## D-2026-09-19-12: one place for position changes
**What.** `self.cell` and `cell.vehicle` are both the vehicle's position and change together in `Vehicle._on_cell_change(new_cell)`: at arrival in a cell (T_arr), at the origin, and on leaving the network (None). The resource lock is separate and is still released tau after the next cell is acquired (T_rel = T_acq + tau). This removes the window in which a slow vehicle was in no cell (lock released, label cleared, not yet arrived) and the one in which a fast vehicle was labelled in two cells.
**Evidence.** Opus principal-engineer review 2026-09-19 (`docs/code-review-2026-09-19.md`), checked by the session against the code and the manuscript. Kerem, 2026-09-19: "Do you think it is a good idea to handle cell's vehicle labels and vehicle's cell labels with callbacks? They change at the same time right?", "like on_cell_change?". Timestamps as the manuscript defines them (tex:232-255): position at T_arr. No timeout(0) needed: SimPy runs a process's code up to its next yield before any woken requester runs.
**Replaces.** Nothing.
**Cited by.** `odca/entity/vehicle.py` `_on_cell_change`, `_delayed_release`, `start`, `_advance_to`, `_exit`.

## D-2026-09-19-11: segment-end vehicles exit from their current lane
**What.** A vehicle bound for the segment end has `destination_lane = None` and leaves from any lane; off-ramp traffic still needs lane 1. Applies to generated and initially placed vehicles. It replaces "return to the entry lane", which made through traffic change lanes back and, in the bottleneck, sent a third of the demand toward the closed lane.
**Evidence.** Manuscript tex:874 ("segment-end vehicles exit from their current lane"); Kerem: paper is the spec. Opus principal-engineer review 2026-09-19 (`docs/code-review-2026-09-19.md`), checked by the session against the code and the manuscript. Golden: S1 seed 1 lane changes per km 4.12 to 3.62.
**Replaces.** Nothing.
**Cited by.** `odca/simulation/generator.py` `_sample_destination`, `odca/simulation/engine.py` `seed_vehicles`, `odca/entity/vehicle.py`.

## D-2026-09-19-10: MIT license
**What.** The package is MIT licensed (`LICENSE`, `pyproject.toml`).
**Evidence.** Inherited from paper-odca-des `DECISIONS.md` D-2026-09-19-10 (Kerem, 2026-09-19, `/architect`).
**Replaces.** Nothing.
**Cited by.** `LICENSE`, `pyproject.toml`.

## D-2026-09-19-9: package scope
**What.** This package holds the simulator core, `odca/params.py`, `analysis` with the one 95% interval
function, the NaSch baseline, the viewers as the `[viewer]` extra, and `odca.experiment`. Papers keep
parameter values, scenario definitions, figures and diagnostics.
**Evidence.** Inherited from paper-odca-des `DECISIONS.md` D-2026-09-19-9 (Kerem, 2026-09-19, `/architect`).
**Replaces.** Nothing.
**Cited by.** `ARCHITECTURE.md` Boundaries; HANDOVER N6, N7.

## D-2026-09-19-8: editable dependency, goldens as tests
**What.** Papers declare `odca-des = { path = "../../odca-des", editable = true }`. Each paper's golden
lives in `tests/golden/<paper>/` and `tests/test_golden.py` must pass before a change merges.
**Evidence.** Inherited from paper-odca-des `DECISIONS.md` D-2026-09-19-8 (Kerem, 2026-09-19, `/architect`).
**Replaces.** Nothing.
**Cited by.** `tests/test_golden.py`, `tests/golden/paper_odca_des/scenarios.py`.

## D-2026-09-19-2: parameter types live in odca
**What.** `VehicleParams`, `ODFlow`, `NetworkConfig`, `SimConfig`, `CELL_LENGTH_M` move to
`odca/params.py`; nothing in `odca` imports a paper's `config`.
**Evidence.** Inherited from paper-odca-des `DECISIONS.md` D-2026-09-19-2 (Kerem, 2026-09-19, `/architect`).
**Replaces.** Nothing.
**Cited by.** HANDOVER N2 (not built yet).

## D-2026-09-19-1: project initialised under this doc set
**What.** odca-des starts as a byte-identical move of paper-odca-des `code/odca/` (git history kept with git filter-repo), with the common doc set plus the `generic` additions.
**Evidence.** Kerem's decisions in paper-odca-des `DECISIONS.md`, D-2026-09-19-6 (one central package), -7 (this repo), -8 (editable dependency, goldens as tests), -9 (scope), -10 (MIT). Proof of the move: paper-odca-des golden 24/24 exact from both sides, 2026-09-19.
**Replaces.** Nothing.
**Cited by.** `HANDOVER.md` (the Type stamp).

## D-2026-03-14-1: one RNG stream per source (inherited)
**What.** Every source of randomness (slowdowns, MLC, DLC, the three driver traits, each
generator) has one `SeedSequence` stream shared by all vehicles; a new stream is spawned last.
**Evidence.** paper-odca-des D-2026-03-14-1 (Kerem, STATUS 2026-03-14).
**Replaces.** nothing.
**Cited by.** `odca/rng.py`, `odca/entity/driver.py` (`TraitSampler`).

