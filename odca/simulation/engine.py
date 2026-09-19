"""Simulation engine: orchestrates the ODCA-DES simulation."""

from __future__ import annotations

import logging
from typing import Dict, List

import simpy


from odca.infrastructure.freeway import Freeway
from odca.infrastructure.incident import Incident
from odca.simulation.factory import VehicleFactory
from odca.simulation.generator import ODPair, VehicleGenerator
from odca.entity.vehicle import Vehicle
from odca.entity.controller import AutonomousController
from odca.entity.driver import DriverStreams, TraitSampler
from odca.params import ConfigMixin, SimConfig
from odca.rng import RNGRegistry

logger = logging.getLogger(__name__)


class CountingEnvironment(simpy.Environment):
    """A SimPy environment that counts the events it processes.

    `events_processed` is the paper's event count (D-2026-09-19-20).
    """

    def __init__(self):
        """Start with no processed events."""
        super().__init__()
        self.events_processed = 0

    def step(self):
        """Process the next event and count it."""
        self.events_processed += 1
        super().step()


class Simulation(ConfigMixin):
    """One ODCA-DES run: freeway, generators, AV controller and the RNG streams."""

    Config = SimConfig

    def __init__(self, cfg: SimConfig):
        """Validate `cfg` (once per run, D-2026-09-19-23) and build the run.

        Args:
            cfg: the run config, as a `SimConfig`, a mapping or a YAML path.
        """
        config = self.cfg = self.validate_config(cfg)

        # Central RNG registry: all randomness flows from this master seed
        self.rng_registry = RNGRegistry(master_seed=config.seed)

        # Reset vehicle IDs
        Vehicle._id_counter = 0

        # Create SimPy environment
        self.env = CountingEnvironment()

        # Build freeway
        net = config.network
        self.freeway = Freeway(self.env, net)

        self.controller = AutonomousController(config.controller, self.env)

        # RNG streams, one per source of randomness, spawned in this fixed order: the
        # decision streams, the trait streams, one per OD pair, then initial_vehicle_type
        streams = DriverStreams.spawn(self.rng_registry)
        self.traits = TraitSampler.spawn(self.rng_registry)
        self.factory = VehicleFactory(self.env, config, streams, self.traits, self.controller)

        # Vehicles placed at t=0 (initial condition)
        self._seeded_vehicles: List[Vehicle] = []

        self.incidents = [Incident(cfg, self.freeway) for cfg in config.incidents]
        self.generators: List[VehicleGenerator] = []
        for i, od in enumerate(self._od_pairs(config)):
            rng_gen = self.rng_registry.spawn(f"generator_{od.origin}_{od.destination}_{i}")
            self.generators.append(
                VehicleGenerator(self.env, self.freeway, od, config, rng_gen, self.factory))

    def _od_pairs(self, config: SimConfig) -> List[ODPair]:
        """The demand table as OD pairs, in table order, checked against the freeway.

        Args:
            config: the run config holding the demand table.

        Raises:
            ValueError: an unknown origin or destination, or a rate that is not positive.
        """
        pairs = []
        for origin, row in config.demand.items():
            self.freeway.origin(origin)
            for destination, rate in row.items():
                self.freeway.destination(destination)
                if rate <= 0:
                    raise ValueError(f"demand {origin} -> {destination} is {rate} veh/h")
                pairs.append(ODPair(origin, destination, rate))
        return pairs

    def seed_vehicles(self, spacing: int, destination: str):
        """Place vehicles uniformly on all lanes at t=0.

        Args:
            spacing: cells between vehicles (15 cells is about 8.9 veh/km at 7.5 m cells).
            destination: destination name for every placed vehicle, e.g. `end`.
        """
        exit_to = self.freeway.destination(destination)
        num_lanes = self.cfg.network.num_lanes
        num_cells = self.cfg.network.num_cells
        # initial vehicles follow the AV share (D-2026-09-19-19); spawned last, after the
        # generator streams, so the earlier streams keep their seeds
        rng_vehicle_type = self.rng_registry.spawn("initial_vehicle_type")

        for lane_idx in range(1, num_lanes + 1):
            lane = self.freeway.lane(lane_idx)
            for cell_idx in range(0, num_cells, spacing):
                cell = lane.cells[cell_idx]
                if cell._blocked:
                    continue  # skip blocked cells (e.g. lane closure)
                autonomous = rng_vehicle_type.random() < self.cfg.av_penetration
                veh = self.factory.build(autonomous, cell, exit_to)
                self._seeded_vehicles.append(veh)
                self.env.process(veh.start())

        logger.info(
            f"Seeded {len(self._seeded_vehicles)} vehicles "
            f"(spacing={spacing} cells, {num_lanes} lanes)"
        )

    def run(self) -> Dict:
        """Run the simulation and return results."""
        self.env.process(self.controller.run())

        # Start all generators
        for gen in self.generators:
            self.env.process(gen.run())
        for incident in self.incidents:
            self.env.process(incident.run(self.env))

        logger.info(f"Running simulation for {self.cfg.sim_duration}s...")
        self.env.run(until=self.cfg.sim_duration)
        logger.info(
            f"Simulation complete. t={self.env.now:.1f}s, "
            f"RNG streams spawned: {self.rng_registry.num_streams}"
        )

        return self._collect_results()

    def _collect_results(self) -> Dict:
        """Gather all vehicle trajectories and statistics."""
        all_vehicles: List[Vehicle] = []
        all_vehicles.extend(self._seeded_vehicles)
        for gen in self.generators:
            all_vehicles.extend(gen.vehicles)

        completed = [v for v in all_vehicles if v.time_exited is not None]
        active = [v for v in all_vehicles if v.active]

        total_generated = sum(g.num_generated for g in self.generators)

        # Aggregate event counters across all vehicles
        counters = {
            "lane_changes": sum(v.count_lane_changes for v in all_vehicles),
            "lc_failures": sum(v.count_lc_failures + v.driver.count_gap_rejections
                               for v in all_vehicles),
            "slowdowns": sum(v.driver.count_slowdowns for v in all_vehicles),
            "cf_evaluations": sum(v.driver.count_cf_evaluations for v in all_vehicles),
            "speed_evaluations": sum(v.driver.count_speed_evaluations for v in all_vehicles),
            "missed_exits": sum(v.count_missed_exits for v in all_vehicles),
            "av_controller_updates": self.controller.num_updates,
            "simpy_events": self.env.events_processed,
        }

        results = {
            "total_generated": total_generated,
            "total_completed": len(completed),
            "total_active_at_end": len(active),
            "vehicles": all_vehicles,
            "completed_vehicles": completed,
            "counters": counters,
            "config": self.cfg,
        }

        logger.info(
            f"Results: {total_generated} generated, "
            f"{len(completed)} completed, {len(active)} still active"
        )
        logger.info(
            f"Events: {counters['lane_changes']} lane changes, "
            f"{counters['lc_failures']} LC failures, "
            f"{counters['slowdowns']} slowdowns, "
            f"{counters['cf_evaluations']} car-following evals, "
            f"{counters['av_controller_updates']} AV controller updates"
        )
        return results
