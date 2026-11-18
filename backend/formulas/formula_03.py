"""Formula 03: Recency-weighted player phase strike rate.

SR(i,p) = 100 * sum_t(w_t * runs_t) / sum_t(w_t)
summed over the legal balls t faced by player i in phase p.
"""
import numpy as np


def weighted_strike_rate(runs, weights):
    runs = np.asarray(runs, dtype=float)
    weights = np.asarray(weights, dtype=float)
    total_w = weights.sum()
    if total_w <= 0:
        return None
    return float(100.0 * (weights * runs).sum() / total_w)
