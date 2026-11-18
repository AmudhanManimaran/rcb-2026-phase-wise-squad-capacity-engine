"""Formula 02: Recency decay weight.

w_t = 2 ^ (-Age_t / H),  H = half-life in days (methodology default 70).
A performance 70 days old counts half as much as one from today.
"""
import numpy as np


def recency_weight(age_days, half_life: float = 70.0):
    """Vectorised recency weight. Negative ages are clipped to zero."""
    if half_life <= 0:
        raise ValueError("half_life must be positive")
    age = np.maximum(np.asarray(age_days, dtype=float), 0.0)
    w = np.power(2.0, -age / half_life)
    return float(w) if np.ndim(w) == 0 else w
