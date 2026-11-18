"""Formula 06: Expected balls faced per innings in a phase.

B_bar_i(p) = (sum_m w_m * balls_im(p) + k_m * B_prior(slot, p)) / (sum_m w_m + k_m)

m runs over completed matches in which player i was in the batting XI
(including innings where he did not face a ball in that phase), w_m is
the recency weight of match m and B_prior is the batting-slot template.
"""
import numpy as np

# Template of expected legal balls per batting slot and phase (sums: 36 / 60 / 24)
SLOT_BALL_TEMPLATE = {
    1: {"PP": 15.0, "MID": 10.0, "DEATH": 1.0},
    2: {"PP": 14.0, "MID": 10.0, "DEATH": 1.5},
    3: {"PP": 5.0,  "MID": 14.0, "DEATH": 3.0},
    4: {"PP": 1.3,  "MID": 11.0, "DEATH": 4.0},
    5: {"PP": 0.4,  "MID": 7.0,  "DEATH": 4.0},
    6: {"PP": 0.2,  "MID": 4.0,  "DEATH": 4.0},
    7: {"PP": 0.1,  "MID": 2.0,  "DEATH": 3.0},
    8: {"PP": 0.0,  "MID": 1.0,  "DEATH": 2.0},
    9: {"PP": 0.0,  "MID": 0.6,  "DEATH": 0.9},
    10: {"PP": 0.0, "MID": 0.3,  "DEATH": 0.4},
    11: {"PP": 0.0, "MID": 0.1,  "DEATH": 0.2},
}


def prior_balls(slot: int, phase: str) -> float:
    slot = int(min(max(slot, 1), 11))
    return SLOT_BALL_TEMPLATE[slot][phase]


def expected_phase_balls(balls_per_match, match_weights, prior: float, k_matches: float = 2.0) -> float:
    balls = np.asarray(balls_per_match, dtype=float)
    w = np.asarray(match_weights, dtype=float)
    return float(((w * balls).sum() + k_matches * prior) / (w.sum() + k_matches))
