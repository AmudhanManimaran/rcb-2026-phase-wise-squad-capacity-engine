"""Parameter calibration by grid search over a walk-forward backtest.

Fitted only on matches before the validation case so that the final
validation remains out-of-sample.

Stage 1 (projection): half-life, shrinkage k, opponent alpha, venue beta
         minimise the checkpoint MAE objective.
Stage 2 (target weight lambda): minimise |T_base - actual RCB total| on
         completed 20-over (or all-out) RCB innings.
Stage 3 (wicket penalty w): minimise MAE between the DP plan's expected
         20-over wickets and actual wickets.
"""
import itertools
from dataclasses import replace

import numpy as np

from backend.backtesting.chronological_runner import run_chronological
from backend.backtesting.metrics import objective
from backend.engine.season_data import EngineParams, SeasonData
from backend.formulas import base_target

GRID = {
    "half_life_days": [35.0, 50.0, 70.0, 100.0, 140.0],
    "shrinkage_k": [15.0, 30.0, 60.0],
    "opp_alpha": [0.5, 1.0],
    "venue_beta": [0.5, 1.0],
}
LAMBDA_GRID = [0.0, 0.25, 0.5, 0.75, 1.0]
WICKET_GRID = [1.0, 2.0, 4.0, 6.0, 8.0]


def calibrate(data: SeasonData, base: EngineParams, train_match_ids: list[int]) -> dict:
    grid_rows = []
    best, best_obj, best_run = None, float("inf"), None
    for hl, k, a, b in itertools.product(*GRID.values()):
        p = replace(base, half_life_days=hl, shrinkage_k=k, opp_alpha=a, venue_beta=b)
        run = run_chronological(data, p, train_match_ids)
        obj = objective(run["results"])
        grid_rows.append({"half_life_days": hl, "shrinkage_k": k, "opp_alpha": a, "venue_beta": b, "objective": round(obj, 3)})
        if obj < best_obj - 1e-9 or (abs(obj - best_obj) < 1e-9 and hl == 70.0):
            best, best_obj, best_run = p, obj, run

    # Stage 2: target weight lambda
    lam_scores = {}
    for lam in LAMBDA_GRID:
        errs = []
        for mid, rec in best_run["predictions"].items():
            act = rec["actual"]
            if not act["checkpoints"][20]["evaluable"]:
                continue
            pred = rec["prediction"]
            errs.append(abs(base_target(pred["venue"]["venue_par"], pred["capacity_total"], lam) - act["total_runs"]))
        lam_scores[lam] = float(np.mean(errs)) if errs else float("inf")
    best_lam = min(lam_scores, key=lambda x: (lam_scores[x], abs(x - 0.5)))

    # Stage 3: wicket penalty
    from backend.engine.pipeline import predict_match
    w_scores = {}
    p_lam = replace(best, target_lambda=best_lam)
    evaluable = [mid for mid, rec in best_run["predictions"].items() if rec["actual"]["checkpoints"][20]["evaluable"]]
    for w in WICKET_GRID:
        errs = []
        for mid in evaluable:
            pred = predict_match(data, mid, replace(p_lam, wicket_penalty=w))
            planned = pred["plan"]["checkpoints"][-1]["planned_cum_wkts"]
            errs.append(abs(planned - best_run["predictions"][mid]["actual"]["wickets"]))
        w_scores[w] = float(np.mean(errs)) if errs else float("inf")
    best_w = min(w_scores, key=lambda x: (w_scores[x], abs(x - 4.0)))

    fitted = replace(p_lam, wicket_penalty=best_w, param_set="CALIBRATED", param_id=None)
    return {"best": fitted, "objective": round(best_obj, 3), "grid": sorted(grid_rows, key=lambda r: r["objective"]),
            "lambda_scores": lam_scores, "wicket_scores": w_scores, "train_matches": len(train_match_ids)}
