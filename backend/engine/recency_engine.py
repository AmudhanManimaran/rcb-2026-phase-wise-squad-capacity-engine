"""Recency weighting of historical deliveries (formula 02)."""
import pandas as pd

from backend.formulas import recency_weight


def apply_recency(history: pd.DataFrame, half_life: float) -> pd.DataFrame:
    h = history.copy()
    h["w"] = recency_weight(h["age_days"].to_numpy(), half_life) if len(h) else []
    return h


def match_weights(history: pd.DataFrame, half_life: float) -> dict:
    """Recency weight per historical match id."""
    if history.empty:
        return {}
    ages = history.groupby("match_id")["age_days"].first()
    return {int(m): float(recency_weight(a, half_life)) for m, a in ages.items()}
