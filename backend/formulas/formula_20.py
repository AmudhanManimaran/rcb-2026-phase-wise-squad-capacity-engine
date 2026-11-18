"""Formula 20: Backtest error metrics.

AbsErr = |Predicted - Actual|
RelErr = (Predicted - Actual) / Actual
MAE    = mean(AbsErr),  MAPE = mean(|RelErr|),  Bias = mean(Predicted - Actual)
Hit    = AbsErr <= max(tolerance_runs, tolerance_pct * Actual)
"""
import numpy as np

CHECKPOINT_TOLERANCE = {6: 8.0, 16: 14.0, 20: 18.0}


def abs_error(pred: float, actual: float) -> float:
    return float(abs(pred - actual))


def rel_error(pred: float, actual: float):
    return float((pred - actual) / actual) if actual else None


def within_tolerance(pred: float, actual: float, checkpoint_over: int, pct: float = 0.10) -> bool:
    tol = max(CHECKPOINT_TOLERANCE.get(checkpoint_over, 15.0), pct * actual)
    return bool(abs(pred - actual) <= tol)


def mae(preds, actuals) -> float:
    p, a = np.asarray(preds, float), np.asarray(actuals, float)
    return float(np.mean(np.abs(p - a))) if len(p) else float("nan")


def mape(preds, actuals) -> float:
    p, a = np.asarray(preds, float), np.asarray(actuals, float)
    return float(np.mean(np.abs((p - a) / a))) if len(p) else float("nan")


def bias(preds, actuals) -> float:
    p, a = np.asarray(preds, float), np.asarray(actuals, float)
    return float(np.mean(p - a)) if len(p) else float("nan")
