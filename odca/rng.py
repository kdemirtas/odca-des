"""Reproducible random number generation for ODCA-DES.

Uses numpy's SeedSequence to create independent RNG streams for each
source of randomness. This ensures:
  1. Full reproducibility given the same master seed
  2. Independence between streams (no cross-contamination)
  3. One stream per source of randomness, shared by all vehicles (D-2026-03-14-1 in
     paper-odca-des): slowdowns, MLC, DLC, the three driver traits, each generator

Usage:
    rng_registry = RNGRegistry(master_seed=42)
    gen_rng = rng_registry.spawn("vehicle_generation")
    slowdown_rng = rng_registry.spawn("slowdown")
"""

import numpy as np


class RNGRegistry:
    """Central registry for reproducible RNG streams."""

    def __init__(self, master_seed: int = 42):
        self.master_seed = master_seed
        self._seed_seq = np.random.SeedSequence(master_seed)
        self._spawn_count = 0

    def spawn(self, name: str) -> np.random.Generator:
        """Create a new independent RNG stream.

        Args:
            name: Descriptive name for this stream (for documentation/debugging).

        Returns:
            A numpy Generator with an independent bit stream.
        """
        child_seed = self._seed_seq.spawn(1)[0]
        rng = np.random.default_rng(child_seed)
        self._spawn_count += 1
        return rng

    @property
    def num_streams(self) -> int:
        """How many streams have been spawned."""
        return self._spawn_count
