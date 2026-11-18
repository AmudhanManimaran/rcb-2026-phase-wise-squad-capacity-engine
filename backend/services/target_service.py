"""Target planning: run the pipeline for a match, persist and retrieve predictions."""
from backend.database import fetch_all, fetch_one, get_conn
from backend.engine.pipeline import predict_match
from backend.services.common import active_params, clean, save_prediction, season_data


def generate_plan(match_id: int, plan_mode: str | None = None, chase_target: float | None = None,
                  wicket_penalty: float | None = None, xi_player_ids: list[int] | None = None,
                  persist: bool = True) -> dict:
    data = season_data()
    pred = predict_match(data, match_id, active_params(), xi_player_ids=xi_player_ids, plan_mode=plan_mode,
                         chase_target=chase_target, wicket_penalty=wicket_penalty)
    if persist:
        with get_conn() as conn:
            pred["prediction_id"] = save_prediction(conn, pred, "ADHOC")
    return clean(pred)


def load_prediction(prediction_id: int) -> dict | None:
    head = fetch_one("""SELECT p.*, c.param_set, c.half_life_days, c.shrinkage_k, c.opp_alpha, c.venue_beta,
                               c.wicket_penalty AS param_wicket_penalty, c.target_lambda
                        FROM rcb_target_predictions p
                        LEFT JOIN rcb_calibration_parameters c ON c.param_id = p.param_id
                        WHERE p.prediction_id = %s""", (prediction_id,))
    if not head:
        return None
    checkpoints = fetch_all("SELECT * FROM rcb_checkpoint_predictions WHERE prediction_id = %s ORDER BY checkpoint_over",
                            (prediction_id,))
    prev = 0.0
    for c in checkpoints:
        c["planned_phase_wkts"] = round(float(c["planned_cum_wkts"]) - prev, 2)
        prev = float(c["planned_cum_wkts"])
    capacity = fetch_all("""SELECT * FROM rcb_team_phase_capacity WHERE prediction_id = %s
                            ORDER BY CASE phase WHEN 'PP' THEN 1 WHEN 'MID' THEN 2 ELSE 3 END""", (prediction_id,))
    profiles = fetch_all("""SELECT pp.*, p.player_name, p.short_name, p.role FROM rcb_player_phase_profiles pp
                            JOIN rcb_players p ON p.player_id = pp.player_id
                            WHERE pp.prediction_id = %s ORDER BY pp.batting_order, pp.phase""", (prediction_id,))
    venue = fetch_all("""SELECT vp.*, v.venue_code, v.venue_name FROM rcb_venue_phase_profiles vp
                         JOIN venues v ON v.venue_id = vp.venue_id WHERE vp.prediction_id = %s
                         ORDER BY CASE phase WHEN 'PP' THEN 1 WHEN 'MID' THEN 2 ELSE 3 END""", (prediction_id,))
    opponent = fetch_all("""SELECT op.*, t.team_code, t.team_name FROM rcb_opponent_phase_profiles op
                            JOIN opponent_teams t ON t.team_id = op.opponent_id WHERE op.prediction_id = %s
                            ORDER BY CASE phase WHEN 'PP' THEN 1 WHEN 'MID' THEN 2 ELSE 3 END""", (prediction_id,))
    return clean({"prediction": head, "checkpoints": checkpoints, "capacity": capacity, "player_profiles": profiles,
                  "venue": venue, "opponent": opponent})


def latest_prediction_id(match_id: int, prefer: str = "ADHOC") -> int | None:
    row = fetch_one("""SELECT prediction_id FROM rcb_target_predictions WHERE match_id = %s
                       ORDER BY (run_type = %s) DESC, created_at DESC, prediction_id DESC LIMIT 1""", (match_id, prefer))
    return int(row["prediction_id"]) if row else None


def saved_prediction(match_id: int) -> dict | None:
    pid = latest_prediction_id(match_id)
    return load_prediction(pid) if pid else None
