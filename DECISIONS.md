# DECISIONS: odca-des
> One entry per decision, newest first, never edited after the fact: a reversed decision gets a
> new entry that names the one it replaces. Ids are `D-YYYY-MM-DD-n`. Code that implements a
> decision cites the id; `/reviewer` checks the citation both ways. `Source` says where the
> decision came from: Kerem directly, an `ASSUMPTIONS.md` row he accepted or corrected (the row
> then leaves that file, `/next-assumption`), or another project's decision this one inherits.

| Id | Decided | What | Source | Replaces |
|---|---|---|---|---|
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
⚠️ Mine, not Kerem's: readable names instead of the dissertation letters (A-2026-09-19-9); `end`
kept for the lane-drop runs (A-2026-09-19-10); wrong end lane counted as missed (A-2026-09-19-11).

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
**Cited by.** `odca/entity/av_controller.py` `register`; `odca/simulation/engine.py` `seed_vehicles`.

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

