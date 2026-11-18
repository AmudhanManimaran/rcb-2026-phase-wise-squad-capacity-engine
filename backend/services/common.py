"""Shared service helpers: cached season data, active parameters, JSON sanitising, persistence."""
import datetime as dt
import math
import threading
from decimal import Decimal

import numpy as np
import pandas as pd

from backend.database import fetch_one, insert_rows
from backend.engine.season_data import EngineParams, SeasonData

_lock = threading.Lock()
_data: SeasonData | None = None


def season_data(refresh: bool = False) -> SeasonData:
    global _data
    with _lock:
        if _data is None or refresh:
            _data = SeasonData.load()
        return _data


def active_params() -> EngineParams:
    row = fetch_one("SELECT * FROM rcb_calibration_parameters WHERE is_active ORDER BY param_id DESC LIMIT 1")
    return EngineParams.from_row(row) if row else EngineParams()


def clean(obj):
    """Recursively convert numpy/pandas/Decimal/date values into JSON-safe Python types."""
    if isinstance(obj, dict):
        return {str(k): clean(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [clean(v) for v in obj]
    if isinstance(obj, pd.DataFrame):
        return clean(obj.to_dict(orient="records"))
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating, float, Decimal)):
        f = float(obj)
        return None if math.isnan(f) or math.isinf(f) else f
    if isinstance(obj, np.bool_):
        return bool(obj)
    if isinstance(obj, (pd.Timestamp, dt.datetime, dt.date)):
        return obj.date().isoformat() if isinstance(obj, (pd.Timestamp, dt.datetime)) else obj.isoformat()
    if obj is pd.NaT:
        return None
    return obj


def save_prediction(conn, pred: dict, run_type: str, backtest_run_id: int | None = None) -> int:
    """Persist a pipeline prediction and all its analytical children. Returns prediction_id."""
    params = pred["params"]
    pid = insert_rows(conn, "rcb_target_predictions", [{
        "match_id": pred["match_id"], "run_type": run_type, "backtest_run_id": backtest_run_id,
        "param_id": params.get("param_id"), "plan_mode": pred["plan_mode"],
        "history_matches": pred["history_matches"], "history_cutoff": pred["history_cutoff"],
        "venue_par": pred["venue"]["venue_par"], "capacity_total": pred["capacity_total"],
        "capacity_wickets": pred["capacity_wickets"], "t_base": pred["target"]["t_base"],
        "bsi": pred["target"]["bsi"], "t_recommended": pred["target"]["t_recommended"],
        "plan_target": pred["plan_target"], "plan_cost": pred["plan"]["total_cost"], "custom_xi": pred["custom_xi"],
    }], returning="prediction_id")[0]
    mid = pred["match_id"]
    insert_rows(conn, "rcb_player_phase_profiles", [{
        "prediction_id": pid, "match_id": mid, "player_id": r["player_id"], "phase": r["phase"],
        "batting_order": r["batting_order"], "raw_balls": r["raw_balls"], "weighted_balls": r["weighted_balls"],
        "sr_observed": r["sr_observed"], "out_observed": r["out_observed"], "sr": r["sr"], "out_prob": r["out_prob"],
        "exp_balls": r["exp_balls"], "ball_share": r["ball_share"], "appearances": r["appearances"],
        "cold_start": bool(r["cold_start"])} for r in pred["player_profiles"]])
    insert_rows(conn, "rcb_venue_phase_profiles", [{
        "prediction_id": pid, "venue_id": pred["venue"]["venue_id"], "phase": v["phase"],
        "sample_innings": v["sample_innings"], "observed_avg": v["observed_avg"], "venue_avg": v["venue_avg"],
        "league_avg": v["league_avg"], "phase_share": v["phase_share"], "venue_factor": v["venue_factor"]}
        for v in pred["venue"]["phases"]])
    insert_rows(conn, "rcb_opponent_phase_profiles", [{
        "prediction_id": pid, "opponent_id": pred["opponent"]["opponent_id"], "phase": o["phase"],
        "sample_overs": o["sample_overs"], "opp_econ": o["opp_econ"], "league_econ": o["league_econ"],
        "opp_threat": o["opp_threat"]} for o in pred["opponent"]["phases"]])
    insert_rows(conn, "rcb_team_phase_capacity", [{
        "prediction_id": pid, "match_id": mid, "phase": c["phase"], "phase_balls": c["phase_balls"],
        "team_sr": c["team_sr"], "team_out_prob": c["team_out_prob"], "raw_runs": c["raw_runs"],
        "raw_wickets": c["raw_wickets"], "venue_factor": c["venue_factor"], "opp_threat": c["opp_threat"],
        "adj_runs": c["adj_runs"], "adj_wickets": c["adj_wickets"]} for c in pred["capacity"]])
    proj = {p["checkpoint_over"]: p for p in pred["projection"]}
    insert_rows(conn, "rcb_checkpoint_predictions", [{
        "prediction_id": pid, "match_id": mid, "checkpoint_over": c["checkpoint_over"], "phase": c["phase"],
        "projected_runs": proj[c["checkpoint_over"]]["projected_runs"],
        "projected_wkts": proj[c["checkpoint_over"]]["projected_wkts"],
        "target_phase_runs": c["target_phase_runs"], "planned_phase_runs": c["planned_phase_runs"],
        "planned_cum_runs": c["planned_cum_runs"], "planned_cum_wkts": c["planned_cum_wkts"], "intent": c["intent"]}
        for c in pred["plan"]["checkpoints"]])
    return pid
