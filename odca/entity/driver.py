"""Drivers: one driver's traits and the one sampler that draws them (D-2026-09-19-24, N3).

A human driver population (`HumanDriverConfig`) gives means and spreads; each driver's own
values are drawn once, when the vehicle is created: tau and action interval log-normal (always
positive, right-skewed for the occasional slow driver), slowdown probability normal clipped to
[0, 1]. Each draw has its own stream, shared by all drivers, used in that order; a value whose
spread is 0 is not drawn (its stream is not advanced).
"""

from __future__ import annotations

from dataclasses import dataclass, replace

import numpy as np

from odca.params import DriverConfig, HumanDriverConfig
from odca.rng import RNGRegistry


@dataclass(frozen=True, slots=True)
class DriverTraits:
    """One driver's own values."""

    tau: float               # reaction time (s)
    action_interval: float   # time between decisions (s)
    slowdown_prob: float     # chance of a random slowdown per decision

    @classmethod
    def exact(cls, cfg: DriverConfig) -> DriverTraits:
        """The config's values, undrawn (autonomous drivers).

        Args:
            cfg: a driver config.
        """
        return cls(cfg.tau, cfg.action_interval, cfg.slowdown_prob)

    def applied_to(self, cfg: DriverConfig) -> DriverConfig:
        """`cfg` with these traits in place of its means.

        Args:
            cfg: the population config.
        """
        return replace(cfg, tau=self.tau, action_interval=self.action_interval,
                       slowdown_prob=self.slowdown_prob)


def _lognormal(rng: np.random.Generator, mean: float, std: float) -> float:
    """A log-normal draw with the given mean and standard deviation.

    Args:
        rng: the stream.
        mean: mean of the draw.
        std: standard deviation of the draw.
    """
    sigma_ln2 = np.log(1 + (std / mean) ** 2)
    mu_ln = np.log(mean) - sigma_ln2 / 2
    return rng.lognormal(mu_ln, np.sqrt(sigma_ln2))


class TraitSampler:
    """Draws human drivers' traits from three streams: tau, action interval, slowdown."""

    def __init__(self, tau: np.random.Generator, action_interval: np.random.Generator,
                 slowdown_prob: np.random.Generator):
        """A sampler on three streams.

        Args:
            tau: stream for reaction times.
            action_interval: stream for action intervals.
            slowdown_prob: stream for slowdown probabilities.
        """
        self.rng_tau = tau
        self.rng_action_interval = action_interval
        self.rng_slowdown_prob = slowdown_prob

    @classmethod
    def spawn(cls, registry: RNGRegistry) -> TraitSampler:
        """A sampler on three new streams of `registry`, spawned in the fixed order.

        Args:
            registry: the run's RNG registry.
        """
        return cls(registry.spawn("driver_tau"), registry.spawn("driver_action_interval"),
                   registry.spawn("driver_slowdown_param"))

    def draw(self, cfg: HumanDriverConfig) -> DriverTraits:
        """One driver's traits.

        Args:
            cfg: the population: means, spreads and clipping ranges.
        """
        tau, action_interval, slowdown_prob = cfg.tau, cfg.action_interval, cfg.slowdown_prob
        if cfg.tau_std > 0:
            tau = float(np.clip(_lognormal(self.rng_tau, cfg.tau, cfg.tau_std),
                                cfg.tau_min, cfg.tau_max))
        if cfg.action_interval_std > 0:
            drawn = _lognormal(self.rng_action_interval, cfg.action_interval,
                               cfg.action_interval_std)
            action_interval = float(np.clip(drawn, cfg.action_interval_min,
                                            cfg.action_interval_max))
        if cfg.slowdown_prob_std > 0:
            drawn = self.rng_slowdown_prob.normal(cfg.slowdown_prob, cfg.slowdown_prob_std)
            slowdown_prob = float(np.clip(drawn, 0.0, 1.0))
        return DriverTraits(tau, action_interval, slowdown_prob)

    def driver_config(self, cfg: HumanDriverConfig) -> HumanDriverConfig:
        """`cfg` with one freshly drawn driver's traits in place of the means.

        Args:
            cfg: the population config.
        """
        return self.draw(cfg).applied_to(cfg)
