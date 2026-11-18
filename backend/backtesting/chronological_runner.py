"""Chronological (walk-forward) backtest over RCB's IPL 2026 matches.

Each match is predicted with only the matches completed before its date,
then compared with its actual checkpoints. No future information leaks
into earlier predictions.
"""
from backend.backtesting.checkpoint_evaluator import evaluate_checkpoints
from backend.backtesting.match_evaluator import actual_rcb_checkpoints
from backend.backtesting.outcome_classifier import classify_match
from backend.engine.pipeline import predict_match
from backend.engine.season_data import EngineParams, SeasonData


def run_chronological(data: SeasonData, params: EngineParams, match_ids: list[int] | None = None,
                      keep_predictions: bool = True) -> dict:
    ordered = data.matches.sort_values(["match_date", "match_id"])
    ordered = ordered[ordered["status"] == "COMPLETED"]
    if match_ids is not None:
        ordered = ordered[ordered["match_id"].isin(match_ids)]
    predictions, results = {}, []
    for _, m in ordered.iterrows():
        mid = int(m["match_id"])
        pred = predict_match(data, mid, params)
        actual = actual_rcb_checkpoints(data, mid)
        if actual is None:
            continue
        cls = classify_match(pred["projection"], actual)
        for row in evaluate_checkpoints(pred["projection"], actual):
            results.append({"match_id": mid, "classification": cls, **row})
        if keep_predictions:
            predictions[mid] = {"prediction": pred, "actual": actual, "classification": cls}
    return {"predictions": predictions, "results": results}
