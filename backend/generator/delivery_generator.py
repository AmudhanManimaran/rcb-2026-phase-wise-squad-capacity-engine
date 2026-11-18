"""Ball-outcome model used by the synthetic data generator.

A legal ball is either a dismissal (probability q) or a scoring outcome
from {0,1,2,3,4,6}. The scoring distribution is a mixture of a defensive
and an aggressive profile whose weight is solved so that the expected
runs per ball equals the batter's effective strike rate / 100.
"""
import numpy as np

RUN_VALUES = np.array([0, 1, 2, 3, 4, 6])
DEFENSIVE = np.array([0.55, 0.33, 0.07, 0.005, 0.035, 0.01])
AGGRESSIVE = np.array([0.25, 0.25, 0.06, 0.005, 0.24, 0.195])
DEFENSIVE = DEFENSIVE / DEFENSIVE.sum()
AGGRESSIVE = AGGRESSIVE / AGGRESSIVE.sum()
MEAN_DEF = float(RUN_VALUES @ DEFENSIVE)
MEAN_AGG = float(RUN_VALUES @ AGGRESSIVE)

WIDE_PROB = 0.035
LEGBYE_PROB = 0.015
DISMISSALS = (["caught"] * 60 + ["bowled"] * 18 + ["lbw"] * 12 + ["run out"] * 6 + ["stumped"] * 4)


def scoring_distribution(runs_per_ball: float, out_prob: float) -> np.ndarray:
    """Distribution over RUN_VALUES conditional on the ball not being a wicket."""
    cond_mean = runs_per_ball / max(1e-6, 1.0 - out_prob)
    t = (cond_mean - MEAN_DEF) / (MEAN_AGG - MEAN_DEF)
    t = min(max(t, 0.0), 1.0)
    return (1 - t) * DEFENSIVE + t * AGGRESSIVE


def simulate_ball(rng: np.random.Generator, runs_per_ball: float, out_prob: float) -> dict:
    """Simulate one delivery. Returns runs, extras, legality and wicket flag."""
    out_prob = float(min(max(out_prob, 0.005), 0.35))
    runs_per_ball = float(min(max(runs_per_ball, 0.3), 3.2))
    u = rng.random()
    if u < WIDE_PROB:
        return dict(runs_batter=0, runs_extras=1, extra_type="WIDE", is_legal=False, is_wicket=False, dismissal_kind=None)
    if u < WIDE_PROB + LEGBYE_PROB:
        return dict(runs_batter=0, runs_extras=1, extra_type="LEGBYE", is_legal=True, is_wicket=False, dismissal_kind=None)
    if rng.random() < out_prob:
        return dict(runs_batter=0, runs_extras=0, extra_type=None, is_legal=True, is_wicket=True,
                    dismissal_kind=DISMISSALS[rng.integers(len(DISMISSALS))])
    runs = int(rng.choice(RUN_VALUES, p=scoring_distribution(runs_per_ball, out_prob)))
    return dict(runs_batter=runs, runs_extras=0, extra_type=None, is_legal=True, is_wicket=False, dismissal_kind=None)
