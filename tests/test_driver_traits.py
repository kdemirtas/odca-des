"""The one trait sampler (N3): clipped draws, fixed stream order, no draw at zero spread."""

import numpy as np

from odca.entity.driver import DriverTraits, TraitSampler
from odca.params import HumanDriverConfig, LogisticLaneChangeConfig

LANE_CHANGE = LogisticLaneChangeConfig(mlc_k=8.0, mlc_r0=0.3, dlc_k=3.0, dlc_v0=1.0,
                                       dlc_cooldown=10.0, safety_gap_front=2.0,
                                       safety_gap_rear=2.0)
POPULATION = HumanDriverConfig(tau=1.5, tau_std=0.3, action_interval=1.0,
                               action_interval_std=0.2, slowdown_prob=0.15,
                               slowdown_prob_std=0.05, slowdown_delta=0.5, look_ahead=10,
                               look_behind=10, lane_change=LANE_CHANGE)


def _sampler(seed=5):
    return TraitSampler(*(np.random.default_rng(s) for s in np.random.SeedSequence(seed).spawn(3)))


def test_draws_stay_in_their_ranges():
    sampler = _sampler()
    for _ in range(5000):
        t = sampler.draw(POPULATION)
        assert 0.5 <= t.tau <= 3.0 and 0.3 <= t.action_interval <= 3.0
        assert 0.0 <= t.slowdown_prob <= 1.0


def test_means_match_the_population():
    sampler = _sampler(11)
    taus = [sampler.draw(POPULATION).tau for _ in range(20000)]
    assert abs(np.mean(taus) - 1.5) < 0.02


def test_zero_spread_draws_nothing():
    from dataclasses import replace
    exact = replace(POPULATION, tau_std=0.0, action_interval_std=0.0, slowdown_prob_std=0.0)
    sampler = _sampler()
    before = sampler.rng_tau.bit_generator.state
    assert sampler.draw(exact) == DriverTraits.exact(exact)
    assert sampler.rng_tau.bit_generator.state == before
