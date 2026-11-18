"""Aggregate backtest metrics (formula 20)."""
import numpy as np

from backend.formulas import bias, mae, mape


def summarise(results: list[dict], validation_match_id: int | None = None) -> dict:
    out = {"matches_evaluated": len({r["match_id"] for r in results})}
    for over in (6, 16, 20):
        ev = [r for r in results if r["checkpoint_over"] == over and r["evaluable"]]
        p = [r["predicted_runs"] for r in ev]
        a = [r["actual_runs"] for r in ev]
        out[f"n_{over}"] = len(ev)
        out[f"mae_{over}"] = round(mae(p, a), 2) if ev else None
        out[f"mape_{over}"] = round(mape(p, a), 4) if ev else None
        out[f"bias_{over}"] = round(bias(p, a), 2) if ev else None
        out[f"hit_{over}"] = round(float(np.mean([r["within_tolerance"] for r in ev])), 3) if ev else None
        if over == 20:
            out["wicket_mae_20"] = round(mae([r["predicted_wkts"] for r in ev], [r["actual_wkts"] for r in ev]), 2) if ev else None
    ev_all = [r for r in results if r["evaluable"]]
    out["hit_rate"] = round(float(np.mean([r["within_tolerance"] for r in ev_all])), 3) if ev_all else None
    if validation_match_id is not None:
        v = [r for r in results if r["match_id"] == validation_match_id and r["checkpoint_over"] == 20 and r["evaluable"]]
        out["validation_match"] = validation_match_id
        out["validation_abs_err"] = v[0]["abs_error"] if v else None
    return out


def objective(results: list[dict]) -> float:
    """Calibration objective: mean absolute error over all evaluable checkpoints, 20-over weighted x2."""
    num = den = 0.0
    for r in results:
        if r["evaluable"]:
            w = 2.0 if r["checkpoint_over"] == 20 else 1.0
            num += w * r["abs_error"]
            den += w
    return num / den if den else float("inf")
