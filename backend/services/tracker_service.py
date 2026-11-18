"""Live innings tracker: deficit vs plan and remaining-phase recommendations."""
from backend.database import fetch_all, fetch_one, get_conn, insert_rows
from backend.engine.deficit_solver import evaluate_state, overs_text, parse_overs
from backend.formulas import PHASES
from backend.services.common import clean, season_data
from backend.services.target_service import generate_plan, latest_prediction_id, load_prediction


def _plan_inputs(prediction_id: int):
    pred = load_prediction(prediction_id)
    if pred is None:
        raise ValueError(f"Prediction {prediction_id} not found")
    plan = [{"phase": c["phase"], "planned_phase_runs": float(c["planned_phase_runs"]),
             "planned_phase_wkts": float(c["planned_phase_wkts"])} for c in pred["checkpoints"]]
    capacity = {c["phase"]: {"adj_runs": float(c["adj_runs"]), "adj_wickets": float(c["adj_wickets"])}
                for c in pred["capacity"]}
    return pred, plan, capacity


def _resolve_prediction(match_id: int, prediction_id: int | None) -> int:
    if prediction_id:
        return int(prediction_id)
    pid = latest_prediction_id(match_id)
    if pid is None:
        pid = generate_plan(match_id)["prediction_id"]
    return pid


def update_state(match_id: int, overs: str, runs: int, wickets: int, prediction_id: int | None = None) -> dict:
    balls = parse_overs(overs)
    if not (0 <= wickets <= 10) or runs < 0:
        raise ValueError("runs must be >= 0 and wickets between 0 and 10")
    pid = _resolve_prediction(match_id, prediction_id)
    pred, plan, capacity = _plan_inputs(pid)
    state = evaluate_state(plan, capacity, balls, runs, wickets, float(pred["prediction"]["plan_target"]))
    with get_conn() as conn:
        tid = insert_rows(conn, "rcb_live_tracker", [{
            "match_id": match_id, "prediction_id": pid, "overs_text": overs_text(balls), "legal_balls": balls,
            "runs": runs, "wickets": wickets, "current_phase": state["current_phase"],
            "expected_runs": state["expected_runs"], "deficit": state["deficit"],
            "projected_total": state["projected_total"], "status": state["status"]}], returning="tracker_id")[0]
        insert_rows(conn, "rcb_deficit_recommendations", [{
            "tracker_id": tid, "phase": r["phase"], "balls_remaining": r["balls_remaining"],
            "efficiency": r["efficiency"], "planned_runs": r["planned_runs"], "extra_runs": r["extra_runs"],
            "revised_runs": r["revised_runs"], "required_rr": r["required_rr"], "capacity_rr": r["capacity_rr"],
            "risk_level": r["risk_level"], "is_primary": r["is_primary"]} for r in state["recommendations"]])
    return clean({"tracker_id": tid, "prediction_id": pid, "plan_mode": pred["prediction"]["plan_mode"], **state})


def current_state(match_id: int) -> dict:
    latest = fetch_one("SELECT * FROM rcb_live_tracker WHERE match_id = %s ORDER BY tracker_id DESC LIMIT 1", (match_id,))
    history = fetch_all("""SELECT tracker_id, overs_text, legal_balls, runs, wickets, expected_runs, deficit, status,
                                  projected_total, updated_at FROM rcb_live_tracker
                           WHERE match_id = %s ORDER BY tracker_id""", (match_id,))
    recs = []
    if latest:
        recs = fetch_all("""SELECT * FROM rcb_deficit_recommendations WHERE tracker_id = %s
                            ORDER BY CASE phase WHEN 'PP' THEN 1 WHEN 'MID' THEN 2 ELSE 3 END""", (latest["tracker_id"],))
    return clean({"match_id": match_id, "latest": latest, "recommendations": recs, "history": history})


def recommendation(match_id: int) -> dict:
    latest = fetch_one("SELECT * FROM rcb_live_tracker WHERE match_id = %s ORDER BY tracker_id DESC LIMIT 1", (match_id,))
    if not latest:
        raise LookupError("No tracker state recorded for this match yet")
    pred, plan, capacity = _plan_inputs(int(latest["prediction_id"]))
    state = evaluate_state(plan, capacity, int(latest["legal_balls"]), int(latest["runs"]), int(latest["wickets"]),
                           float(pred["prediction"]["plan_target"]))
    return clean({"tracker_id": latest["tracker_id"], **state})


def reset(match_id: int) -> int:
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("DELETE FROM rcb_live_tracker WHERE match_id = %s", (match_id,))
        return cur.rowcount


def replay(match_id: int, prediction_id: int | None = None) -> dict:
    """Over-by-over replay of RCB's actual innings against the pre-match plan."""
    data = season_data()
    inn = data.innings[(data.innings["match_id"] == match_id) & (data.innings["batting_side"] == "RCB")]
    if inn.empty:
        raise LookupError("No RCB innings for this match")
    if prediction_id is None:
        row = fetch_one("""SELECT prediction_id FROM rcb_target_predictions WHERE match_id = %s AND run_type = 'BACKTEST'
                           ORDER BY prediction_id DESC LIMIT 1""", (match_id,))
        prediction_id = int(row["prediction_id"]) if row else _resolve_prediction(match_id, None)
    pred, plan, capacity = _plan_inputs(prediction_id)
    target = float(pred["prediction"]["plan_target"])
    d = data.deliveries[data.deliveries["innings_id"] == int(inn.iloc[0]["innings_id"])].sort_values("delivery_id")

    states = []
    last_over = int(d["over_no"].max()) if len(d) else 0
    for over in range(1, last_over + 1):
        upto = d[d["over_no"] <= over]
        balls = int(upto["is_legal"].sum())
        runs = int(upto["runs_total"].sum())
        wkts = int(upto["is_wicket"].sum())
        s = evaluate_state(plan, capacity, balls, runs, wkts, target)
        s["over"] = over
        s["over_runs"] = int(d[d["over_no"] == over]["runs_total"].sum())
        states.append(s)
    planned_worm, acc = [], 0.0
    for c in plan:
        n = {"PP": 6, "MID": 10, "DEATH": 4}[c["phase"]]
        for _ in range(n):
            acc += c["planned_phase_runs"] / n
            planned_worm.append(round(acc, 2))
    return clean({"match_id": match_id, "prediction_id": prediction_id, "plan_mode": pred["prediction"]["plan_mode"],
                  "plan_target": target, "planned_worm": planned_worm, "states": states,
                  "checkpoints": pred["checkpoints"]})
