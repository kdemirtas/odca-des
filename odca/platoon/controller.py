"""PlatoonController: the autonomous controller with platoon management (D-2026-11-05-1).

Besides deciding for every autonomous driver each `dt`, as `AutonomousController` does, it runs a
platoon management loop every `PlatoonConfig.dt` with four phases in order:

0. the chain is checked: a member that left the road leaves its platoon, and the platoon is cut
   where a member is out of the leader's lane or another vehicle is between two members;
1. splits: a member within `split_lookahead` cells of its destination and outside its
   destination lane leaves, so it can change lanes on its own; if every member leaves, the
   platoon is dissolved;
2. formation: solo autonomous vehicles in one lane, with no other vehicle between them, are
   grouped, front first;
3. merges: a platoon just behind another in the same lane, with no vehicle between, joins it.

The strategy decides which vehicles are compatible: naive (any two), emp (the same destination)
or dcp (destinations at most `dest_cluster_threshold` cells apart). Platooning draws no random
number, so it adds no RNG stream.

A member leaving for its destination, by the split phase or by leaving the road, makes a
destination split only where it separates different destinations (once per destination and
platoon line), an end-of-trip dissolution where the platoon ends with nobody bound elsewhere,
and a size-one dissolution where one member bound elsewhere is left (D-2026-11-05-3).
"""

from __future__ import annotations

import logging
from collections import Counter
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional

import simpy

from odca.entity.controller import AutonomousController
from odca.entity.driver import DriverStreams
from odca.entity.vehicle import Vehicle
from odca.params import AutonomousDriverConfig, ControllerConfig
from odca.platoon.driver import PlatoonDriver
from odca.platoon.platoon import Platoon

logger = logging.getLogger(__name__)


class PlatoonStrategy(Enum):
    """Which vehicles may form a platoon; `PlatoonStrategy(name)` raises on an unknown name."""

    NAIVE = "naive"   # proximity and speed only
    EMP = "emp"       # exact match: the same destination
    DCP = "dcp"       # destination cluster: destinations close together


@dataclass(frozen=True, slots=True)
class PlatoonStatistics:
    """What the platoon management did in one run."""

    num_active_platoons: int      # at the end of the run
    num_platooned_vehicles: int   # at the end of the run
    avg_av_unit_size_on_road: float  # diagnostic only: AVs on the road per AV unit, time
                                     # average after the warm-up; m-bar as the paper defines
                                     # it is the section count, `odca.platoon.measures`
    avg_platoon_size: float       # mean size of the platoons (m >= 2), same samples
    max_platoon_size: int         # the largest platoon sampled after the warm-up
    total_formations: int
    total_merges: int
    destination_splits: int       # cuts separating different destinations, once per
                                  # destination and platoon line (0 under emp)
    end_of_trip_dissolutions: int # platoons ended with no member bound elsewhere
    size_one_dissolutions: int    # platoons left with one vehicle by a split or a cut
    chain_breaks: int             # cuts where a member left the lane or a vehicle cut in
    lane_changes_blocked: int     # leader lane changes refused with train_lane_changes off
    train_lane_changes: int       # leader lane changes granted to the whole train
    train_lc_refused_exit_side: int  # refused: it would move a member away from its exit lane
    train_lc_refused_room: int    # refused: the target lane had no room for the train
    # with train_lane_changes on: per platoon size m (as a string, for JSON), the leader's
    # lane-change decisions that passed the exit-side rule (attempts: the room was checked) and
    # those the target lane had room for (granted); their ratio estimates the contiguous-gap
    # probability per decision
    train_lc_attempts_by_size: Dict[str, int] = field(default_factory=dict)
    train_lc_granted_by_size: Dict[str, int] = field(default_factory=dict)
    # formations by "m,D": platoon size and number of distinct destination cells at formation
    formations_by_size_destinations: Dict[str, int] = field(default_factory=dict)


class PlatoonController(AutonomousController):
    """Central controller for the autonomous drivers, forming and managing platoons."""

    def __init__(self, cfg: ControllerConfig, env: simpy.Environment, warmup: float = 0.0):
        """A controller that platoons according to `cfg.platoon`.

        Args:
            cfg: the controller config; its `platoon` must be set.
            env: the SimPy environment it runs in.
            warmup: seconds before the platoon sizes are sampled.

        Raises:
            ValueError: `cfg.platoon` is None.
        """
        if cfg.platoon is None:
            raise ValueError("a PlatoonController needs a platoon config")
        super().__init__(cfg, env)
        self.platoon_cfg = cfg.platoon
        self.strategy = PlatoonStrategy(cfg.platoon.strategy)
        self.warmup = warmup
        self.platoons: List[Platoon] = []
        self._next_platoon_id = 0
        self._size_samples = 0      # platoon-samples after the warm-up
        self._size_sum = 0          # their sizes, summed
        self._size_max = 0
        self._unit_sum = 0          # AV units (platoons and solo AVs) on the road, summed
        self._unit_av_sum = 0       # AVs on the road, summed
        self.count_formations = 0
        self.count_merges = 0
        self.count_destination_splits = 0
        self.count_end_of_trip_dissolutions = 0
        self.count_size_one_dissolutions = 0
        self.count_chain_breaks = 0
        self.count_train_lc_requests = 0
        self.count_lc_blocked = 0
        self.count_train_lc_refused_exit_side = 0
        self.count_train_lc_refused_room = 0
        self.train_lc_attempts: Counter = Counter()
        self.formations_by_size_destinations: Counter = Counter()
        self.train_lc_granted: Counter = Counter()

    def driver_for(self, cfg: AutonomousDriverConfig, streams: DriverStreams) -> PlatoonDriver:
        """A new driver that can join a platoon.

        Args:
            cfg: the autonomous driver config.
            streams: the shared decision streams.
        """
        return PlatoonDriver(cfg, streams, self)

    def active_platoons(self) -> List[Platoon]:
        """The platoons that still exist."""
        return [p for p in self.platoons if p.active]

    def run(self):
        """SimPy process: platoon management alongside the per-dt decisions."""
        self.env.process(self._management_loop())
        yield from super().run()

    def _management_loop(self):
        """Every platoon dt: drop, split, form, merge, then sample the sizes."""
        while True:
            yield self.env.timeout(self.platoon_cfg.dt)
            self.platoons = self.active_platoons()
            on_road = [d.vehicle for d in self.active_drivers() if d.vehicle.cell is not None]
            if on_road:
                self._check_chains()
                self._evaluate_splits()
                self._evaluate_formations(on_road)
                self._evaluate_merges()
            if self.env.now >= self.warmup:
                self._sample_sizes(on_road)

    # ------------------------------------------------------------------
    # Building and taking apart
    # ------------------------------------------------------------------

    def form(self, members: List[Vehicle]) -> Platoon:
        """A new platoon of `members`, front first, managed from now on.

        Args:
            members: two or more solo vehicles driven by `PlatoonDriver`s, front first.
        """
        platoon = Platoon(self._next_platoon_id, members)
        self._next_platoon_id += 1
        self.platoons.append(platoon)
        self.count_formations += 1
        destinations = len({m.destination_cell_idx for m in members})
        self.formations_by_size_destinations[f"{len(members)},{destinations}"] += 1
        return platoon

    def _remove(self, platoon: Platoon, member: Vehicle):
        """Take `member` out of `platoon`; a rear part cut off becomes its own platoon.

        Args:
            platoon: an active platoon.
            member: one of its members.
        """
        inherited = set(platoon.split_destinations)
        behind = platoon.remove(member)
        if behind is not None:
            self._adopt(behind).split_destinations |= inherited
        if not platoon.active:
            self.count_size_one_dissolutions += 1

    def _cut(self, platoon: Platoon, idx: int):
        """Cut `platoon` in front of member `idx`; a rear part of two or more drives on as its
        own platoon.

        Args:
            platoon: an active platoon.
            idx: the first member of the rear part, 1 to size - 1.
        """
        inherited = set(platoon.split_destinations)
        back = platoon.split_at(idx)
        if len(back) >= 2:
            self._adopt(back).split_destinations |= inherited
        if not platoon.active:
            self.count_size_one_dissolutions += 1

    def _adopt(self, members: List[Vehicle]) -> Platoon:
        """Manage `members`, the rear part of a cut platoon, as a platoon of its own.

        Args:
            members: two or more vehicles, front first.
        """
        platoon = Platoon(self._next_platoon_id, members)
        self.platoons.append(platoon)
        self._next_platoon_id += 1
        return platoon

    def _sample_sizes(self, on_road: List[Vehicle]):
        """Add this instant to the time averages of the unit and platoon sizes.

        Args:
            on_road: the autonomous vehicles on the road at the start of this cycle.
        """
        avs = [v for v in on_road if v.active and v.cell is not None]
        platoons = self.active_platoons()
        solo = sum(1 for v in avs if v.driver.platoon is None)
        self._unit_av_sum += len(avs)
        self._unit_sum += solo + len(platoons)
        for platoon in platoons:
            self._size_samples += 1
            self._size_sum += platoon.size
            self._size_max = max(self._size_max, platoon.size)

    # ------------------------------------------------------------------
    # Phase 0: the chain
    # ------------------------------------------------------------------

    def _check_chains(self):
        """Members that left the road leave; a platoon is cut where its chain is broken.

        A rear part cut off is appended to `platoons` and checked in the same pass.
        """
        i = 0
        while i < len(self.platoons):
            platoon = self.platoons[i]
            i += 1
            for member in platoon.members:
                if (platoon.active and member in platoon.members
                        and (not member.active or member.cell is None)):
                    self._leave_for_destination(platoon, [member])
            while platoon.active:
                idx = self._first_break(platoon)
                if idx is None:
                    break
                self._cut(platoon, idx)
                self.count_chain_breaks += 1

    @staticmethod
    def _first_break(platoon: Platoon) -> Optional[int]:
        """The first member out of the leader's lane or with another vehicle ahead of it
        before the previous member, or None for an unbroken chain.

        Args:
            platoon: an active platoon whose members are all on the road.
        """
        members = platoon.members
        lane = members[0].cell.lane
        for idx in range(1, len(members)):
            ahead, member = members[idx - 1], members[idx]
            if member.cell.lane is not lane or not _clear_between(ahead, member):
                return idx
        return None

    # ------------------------------------------------------------------
    # Phase 1: splits
    # ------------------------------------------------------------------

    def _evaluate_splits(self):
        """Members near their destination and outside its lane leave their platoon.

        A member leaves once its destination is at most `split_lookahead` cells ahead and it is
        not in the destination's lane, so it can make its own mandatory lane changes; a member
        already in that lane drives on in the platoon until it leaves the road.
        """
        for platoon in list(self.active_platoons()):
            leaving = [m for m in platoon.members if self._must_leave(m)]
            if leaving:
                self._leave_for_destination(platoon, leaving)

    def _must_leave(self, member: Vehicle) -> bool:
        """Whether `member` is near its destination and outside its destination lane.

        Args:
            member: a platoon member on the road.
        """
        destination = member.destination_cell_idx
        if (destination is None or member.cell is None
                or member.destination_lane in (None, member.cell.lane.idx)):
            return False
        return 0 < destination - member.cell.idx <= self.platoon_cfg.split_lookahead

    def _leave_for_destination(self, platoon: Platoon, leaving: List[Vehicle]):
        """Let `leaving` go for their destinations, counting what the departure is
        (D-2026-11-05-3).

        A destination split separates members bound for different destinations: it is counted
        once for each destination cell that leaves while a member bound elsewhere drives on,
        and only the first time that destination leaves this platoon's line, so members with
        the same exit leaving in different cycles count once, and an emp platoon never splits.
        A departure that leaves no member, or only members bound where the leavers are, is the
        end of the trip: one end-of-trip dissolution once the platoon is gone. A platoon left
        with one member bound elsewhere is a size-one dissolution.

        Args:
            platoon: an active platoon.
            leaving: some or all of its members.
        """
        members = platoon.members
        leaving = [m for m in leaving if m in members]
        if not leaving:
            return
        remaining = [m for m in members if m not in leaving]
        separated = {m.destination_cell_idx for m in leaving
                     if any(r.destination_cell_idx != m.destination_cell_idx
                            for r in remaining)} - platoon.split_destinations
        self.count_destination_splits += len(separated)
        platoon.split_destinations |= separated
        inherited = set(platoon.split_destinations)
        first = min(members.index(m) for m in leaving)
        if remaining and first > 0 and all(m in leaving for m in members[first:]):
            platoon.split_at(first)
        else:
            for member in leaving:
                if not platoon.active or member not in platoon.members:
                    continue
                behind = platoon.remove(member)
                if behind is not None:
                    self._adopt(behind).split_destinations |= inherited
        if platoon.active:
            return
        if separated or (remaining and any(
                r.destination_cell_idx != m.destination_cell_idx
                for r in remaining for m in leaving)):
            self.count_size_one_dissolutions += 1
        else:
            self.count_end_of_trip_dissolutions += 1

    # ------------------------------------------------------------------
    # Phase 2: formation
    # ------------------------------------------------------------------

    def _evaluate_formations(self, on_road: List[Vehicle]):
        """Group the solo vehicles of each lane into platoons.

        Args:
            on_road: the autonomous vehicles on the road.
        """
        solo_by_lane: Dict[int, List[Vehicle]] = {}
        for vehicle in on_road:
            if vehicle.driver.platoon is None:
                solo_by_lane.setdefault(vehicle.cell.lane.idx, []).append(vehicle)
        for lane_idx in sorted(solo_by_lane):
            solos = sorted(solo_by_lane[lane_idx], key=lambda v: v.cell.idx, reverse=True)
            self._form_in_lane(solos)

    def _form_in_lane(self, solos: List[Vehicle]):
        """Greedy formation in one lane, front first.

        Each candidate leader takes the vehicles behind it as followers while the gap to the
        previous member is at most `formation_gap` cells with no other vehicle in it, skipping one whose speed differs from the
        leader's by more than `formation_speed_diff`, that is not compatible, or that shares
        less than `min_shared_path` cells of road with the leader.

        Args:
            solos: solo vehicles of one lane, front first.
        """
        cfg = self.platoon_cfg
        used = set()
        for i, leader in enumerate(solos):
            if leader.id in used:
                continue
            followers: List[Vehicle] = []
            for candidate in solos[i + 1:]:
                if candidate.id in used:
                    continue
                last = followers[-1] if followers else leader
                if last.cell.idx - candidate.cell.idx > cfg.formation_gap:
                    break
                if not _clear_between(last, candidate):
                    break
                if abs(candidate.speed - leader.speed) > cfg.formation_speed_diff:
                    continue
                if not self.compatible(leader, candidate):
                    continue
                if not self._sufficient_shared_path(leader, candidate):
                    continue
                followers.append(candidate)
                if 1 + len(followers) >= cfg.max_platoon_size:
                    break
            if not followers:
                continue
            platoon = self.form([leader] + followers)
            used.update(m.id for m in platoon.members)
            logger.debug("t=%.2f  formed %s (%s)", self.env.now, platoon, self.strategy.value)

    def compatible(self, first: Vehicle, second: Vehicle) -> bool:
        """Whether the strategy lets `first` and `second` drive in one platoon.

        Args:
            first: a vehicle.
            second: another vehicle.
        """
        if self.strategy is PlatoonStrategy.NAIVE:
            return True
        d1, d2 = first.destination_cell_idx, second.destination_cell_idx
        if d1 is None or d2 is None:
            return False
        if self.strategy is PlatoonStrategy.EMP:
            return d1 == d2
        return abs(d1 - d2) <= self.platoon_cfg.dest_cluster_threshold

    def _sufficient_shared_path(self, first: Vehicle, second: Vehicle) -> bool:
        """Whether the two still drive `min_shared_path` cells together.

        The shared path is min(d1, d2) - min(x1, x2): from the rear one's cell to the nearer
        destination.

        Args:
            first: a vehicle.
            second: another vehicle.
        """
        if self.platoon_cfg.min_shared_path <= 0:
            return True
        d1, d2 = first.destination_cell_idx, second.destination_cell_idx
        if d1 is None or d2 is None:
            return True
        shared = min(d1, d2) - min(first.cell.idx, second.cell.idx)
        return shared >= self.platoon_cfg.min_shared_path

    # ------------------------------------------------------------------
    # Phase 3: merges
    # ------------------------------------------------------------------

    def _evaluate_merges(self):
        """A platoon whose leader is within `formation_gap` of the tail ahead, with no vehicle
        between, joins it."""
        cfg = self.platoon_cfg
        by_lane: Dict[int, List[Platoon]] = {}
        for platoon in self.active_platoons():
            lane = platoon.lane_idx()
            if lane is not None:
                by_lane.setdefault(lane, []).append(platoon)
        for lane_idx in sorted(by_lane):
            platoons = sorted(by_lane[lane_idx], key=lambda p: p.leader.cell.idx, reverse=True)
            i = 0
            while i < len(platoons) - 1:
                ahead, behind = platoons[i], platoons[i + 1]
                gap = ahead.tail.cell.idx - behind.leader.cell.idx
                if (gap > cfg.formation_gap
                        or not _clear_between(ahead.tail, behind.leader)
                        or ahead.size + behind.size > cfg.max_platoon_size
                        or not self.compatible(ahead.leader, behind.leader)):
                    i += 1
                    continue
                ahead.merge(behind)
                self.count_merges += 1
                platoons.pop(i + 1)

    # ------------------------------------------------------------------
    # Statistics
    # ------------------------------------------------------------------

    def statistics(self) -> PlatoonStatistics:
        """What the platoon management did, for the run's result."""
        active = self.active_platoons()
        return PlatoonStatistics(
            num_active_platoons=len(active),
            num_platooned_vehicles=sum(p.size for p in active),
            avg_av_unit_size_on_road=(self._unit_av_sum / self._unit_sum if self._unit_sum else 0.0),
            avg_platoon_size=(self._size_sum / self._size_samples if self._size_samples
                              else 0.0),
            max_platoon_size=self._size_max,
            total_formations=self.count_formations,
            total_merges=self.count_merges,
            destination_splits=self.count_destination_splits,
            end_of_trip_dissolutions=self.count_end_of_trip_dissolutions,
            size_one_dissolutions=self.count_size_one_dissolutions,
            chain_breaks=self.count_chain_breaks,
            lane_changes_blocked=self.count_lc_blocked,
            train_lane_changes=self.count_train_lc_requests,
            train_lc_refused_exit_side=self.count_train_lc_refused_exit_side,
            train_lc_refused_room=self.count_train_lc_refused_room,
            train_lc_attempts_by_size={str(m): n for m, n in sorted(self.train_lc_attempts.items())},
            train_lc_granted_by_size={str(m): n for m, n in sorted(self.train_lc_granted.items())},
            formations_by_size_destinations=dict(sorted(
                self.formations_by_size_destinations.items())),
        )

    def placed_platoon(self, members: List[Vehicle]) -> Optional[Platoon]:
        """A platoon of vehicles placed on the road as one (not counted as a formation).

        Args:
            members: vehicles placed in consecutive cells of one lane, front first.
        """
        if len(members) < 2:
            return None
        platoon = Platoon(self._next_platoon_id, members)
        self._next_platoon_id += 1
        self.platoons.append(platoon)
        return platoon


def _clear_between(ahead: Vehicle, behind: Vehicle) -> bool:
    """Whether no other vehicle is in the cells between `behind` and `ahead` in their lane.

    Args:
        ahead: a vehicle on the road.
        behind: a vehicle in the same lane, behind it.
    """
    cells = behind.cell.lane.cells
    return all(c.vehicle is None for c in cells[behind.cell.idx + 1:ahead.cell.idx])
