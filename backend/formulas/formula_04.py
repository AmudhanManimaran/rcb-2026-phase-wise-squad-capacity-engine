"""Formula 04: Recency-weighted player phase out probability.

OutProb(i,p) = sum_t(w_t * 1[out_t]) / sum_t(w_t)
"""
import numpy as np


def weighted_out_probability(outs, weights):
    outs = np.asarray(outs, dtype=float)
    weights = np.asarray(weights, dtype=float)
    total_w = weights.sum()
    if total_w <= 0:
        return None
    return float((weights * outs).sum() / total_w)
