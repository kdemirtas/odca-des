"""Reproducible random number generation for ODCA-DES.

Uses numpy's SeedSequence to create independent RNG streams for each
source of randomness. This ensures:
  1. Full reproducibility given the same master seed
  2. Independence between streams (no cross-contamination)
  3. Each vehicle gets its own RNG for behavioral stochasticity

Usage:
    rng_registry = RNGRegistry(master_seed=42)
    gen_rng = rng_registry.spawn("vehicle_generation")
    veh_rng = rng_registry.spawn("vehicle_123_behavior")
"""

from typing import Dict

import numpy as np


class RNGRegistry:
    """Central registry for reproducible RNG streams."""

    def __init__(self, master_seed: int = 42):
        self.master_seed = master_seed
        self._seed_seq = np.random.SeedSequence(master_seed)
        self._streams: Dict[str, np.random.Generator] = {}
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
        self._streams[name] = rng
        self._spawn_count += 1
        return rng

    def get(self, name: str) -> np.random.Generator:
        """Retrieve a previously created stream by name."""
        return self._streams[name]

    @property
    def num_streams(self) -> int:
        return self._spawn_count
