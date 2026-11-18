"""Backtesting, calibration, dashboard and descriptive analytics."""
import json

from backend.backtesting.chronological_runner import run_chronological
from backend.backtesting.metrics import summarise
from backend.database import fetch_all, fetch_one, get_conn, insert_rows
from backend.engine.calibration_engine import calibrate
from backend.services.common import active_params, clean, save_prediction, season_data
from backend.services.target_service import load_prediction


def _validation_match_id(data) -> int | None:
    v = data.matches[data.matches["is_validation_case"]]
    return int(v.iloc[0]["match_id"]) if len(v) else None


# ---------------------------------------------------------------------- backtest
def run_backtest(use_active: bool = True) -> dict:
    data = season_data(refresh=True)
    params = active_params()
    run = run_chronological(data, params)
    summary = summarise(run["results"], _validation_match_id(data))
    with get_conn() as conn:
        run_id = insert_rows(conn, "rcb_backtest_runs", [{
            "param_id": params.param_id, "matches_evaluated": summary["matches_evaluated"],
            "mae_6": summary["mae_6"], "mae_16": summary["mae_16"], "mae_20": summary["mae_20"],
            "mape_20": summary["mape_20"], "bias_20": summary["bias_20"], "hit_rate": summary["hit_rate"],
            "wicket_mae_20": summary["wicket_mae_20"], "validation_match": summary.get("validation_match"),
            "validation_abs_err": summary.get("validation_abs_err")}], returning="backtest_run_id")[0]
        pred_ids = {mid: save_prediction(conn, rec["prediction"], "BACKTEST", run_id)
                    for mid, rec in run["predictions"].items()}
        insert_rows(conn, "rcb_backtest_results", [{
            "backtest_run_id": run_id, "prediction_id": pred_ids[r["match_id"]], "match_id": r["match_id"],
            "checkpoint_over": r["checkpoint_over"], "predicted_runs": r["predicted_runs"],
            "actual_runs": r["actual_runs"], "predicted_wkts": r["predicted_wkts"], "actual_wkts": r["actual_wkts"],
            "abs_error": r["abs_error"], "rel_error": r["rel_error"], "within_tolerance": r["within_tolerance"],
            "evaluable": r["evaluable"], "classification": r["classification"]} for r in run["results"]])
    return clean({"backtest_run_id": run_id, "params": params.as_dict(), "summary": summary})


def run_calibration() -> dict:
    data = season_data(refresh=True)
    vid = _validation_match_id(data)
    cutoff = data.match(vid)["match_date"] if vid else None
    train = [int(m) for m, d in zip(data.matches["match_id"], data.matches["match_date"])
             if cutoff is None or d < cutoff]
    base = active_params()
    res = calibrate(data, base, train)
    b = res["best"]
    notes = {"top_grid": res["grid"][:5], "lambda_scores": res["lambda_scores"], "wicket_scores": res["wicket_scores"],
             "train_match_ids": train}
    with get_conn() as conn:
        pid = insert_rows(conn, "rcb_calibration_parameters", [{
            "param_set": "CALIBRATED", "half_life_days": b.half_life_days, "shrinkage_k": b.shrinkage_k,
            "opp_alpha": b.opp_alpha, "venue_beta": b.venue_beta, "wicket_penalty": b.wicket_penalty,
            "target_lambda": b.target_lambda, "objective_mae": res["objective"], "matches_used": len(train),
            "is_active": True, "notes": json.dumps(clean(notes))}], returning="param_id")[0]
    return clean({"param_id": pid, "best": {**b.as_dict(), "param_id": pid}, "objective": res["objective"],
                  "train_matches": len(train), "top_grid": res["grid"][:10],
                  "lambda_scores": res["lambda_scores"], "wicket_scores": res["wicket_scores"]})


def list_parameters() -> list[dict]:
    return clean(fetch_all("SELECT * FROM rcb_calibration_parameters ORDER BY param_id DESC"))


def activate_parameters(param_id: int) -> dict:
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("UPDATE rcb_calibration_parameters SET is_active = TRUE WHERE param_id = %s", (param_id,))
        if cur.rowcount == 0:
            raise LookupError(f"Parameter set {param_id} not found")
    return clean(fetch_one("SELECT * FROM rcb_calibration_parameters WHERE param_id = %s", (param_id,)))


def latest_run() -> dict | None:
    return fetch_one("""SELECT r.*, c.param_set, c.half_life_days, c.shrinkage_k, c.opp_alpha, c.venue_beta,
                               c.wicket_penalty, c.target_lambda
                        FROM rcb_backtest_runs r LEFT JOIN rcb_calibration_parameters c ON c.param_id = r.param_id
                        ORDER BY r.backtest_run_id DESC LIMIT 1""")


def backtest_results() -> dict:
    run = latest_run()
    if not run:
        return {"run": None, "summary": [], "matches": [], "runs": []}
    rows = fetch_all("SELECT * FROM v_backtest_detail WHERE backtest_run_id = %s ORDER BY match_date, checkpoint_over",
                     (run["backtest_run_id"],))
    matches = {}
    for r in rows:
        m = matches.setdefault(r["match_id"], {k: r[k] for k in ("match_id", "rcb_match_no", "ipl_match_no", "match_date",
                                                                  "opponent_code", "venue_code", "rcb_batting_first",
                                                                  "is_validation_case", "classification")})
        m[f"cp{r['checkpoint_over']}"] = {k: r[k] for k in ("predicted_runs", "actual_runs", "predicted_wkts",
                                                           "actual_wkts", "abs_error", "rel_error",
                                                           "within_tolerance", "evaluable")}
    runs = fetch_all("""SELECT r.backtest_run_id, r.created_at, r.mae_6, r.mae_16, r.mae_20, r.hit_rate, c.param_set
                        FROM rcb_backtest_runs r LEFT JOIN rcb_calibration_parameters c ON c.param_id = r.param_id
                        ORDER BY r.backtest_run_id DESC LIMIT 10""")
    summary = fetch_all("SELECT * FROM v_backtest_summary ORDER BY checkpoint_over")
    return clean({"run": run, "summary": summary, "matches": list(matches.values()), "runs": runs})


def backtest_match(match_id: int) -> dict:
    run = latest_run()
    if not run:
        raise LookupError("No backtest has been run yet")
    row = fetch_one("""SELECT prediction_id FROM rcb_target_predictions
                       WHERE match_id = %s AND backtest_run_id = %s""", (match_id, run["backtest_run_id"]))
    if not row:
        raise LookupError("Match not part of the latest backtest")
    pred = load_prediction(int(row["prediction_id"]))
    results = fetch_all("""SELECT * FROM rcb_backtest_results WHERE backtest_run_id = %s AND match_id = %s
                           ORDER BY checkpoint_over""", (run["backtest_run_id"], match_id))
    phases = fetch_all("""SELECT phase, phase_runs, phase_wickets, phase_balls, phase_run_rate
                          FROM v_phase_innings_summary WHERE match_id = %s AND batting_side = 'RCB'
                          ORDER BY CASE phase WHEN 'PP' THEN 1 WHEN 'MID' THEN 2 ELSE 3 END""", (match_id,))
    match = fetch_one("SELECT * FROM v_rcb_match_summary WHERE match_id = %s", (match_id,))
    return clean({"match": match, "prediction": pred, "results": results, "actual_phases": phases})


# ---------------------------------------------------------------------- dashboard
def dashboard() -> dict:
    matches = fetch_all("SELECT * FROM v_rcb_match_summary ORDER BY match_date")
    done = [m for m in matches if m["status"] == "COMPLETED"]
    wins = sum(1 for m in done if m["winner"] == "RCB")
    phase_avg = fetch_all("""SELECT phase, ROUND(AVG(phase_runs),2) AS avg_runs, ROUND(AVG(phase_wickets),2) AS avg_wkts,
                                    ROUND(AVG(phase_run_rate),2) AS avg_rr, COUNT(*) AS innings
                             FROM v_phase_innings_summary WHERE batting_side = %s
                             GROUP BY phase ORDER BY CASE phase WHEN 'PP' THEN 1 WHEN 'MID' THEN 2 ELSE 3 END""", ("RCB",))
    opp_phase_avg = fetch_all("""SELECT phase, ROUND(AVG(phase_runs),2) AS avg_runs, ROUND(AVG(phase_run_rate),2) AS avg_rr
                                 FROM v_phase_innings_summary WHERE batting_side = 'OPP'
                                 GROUP BY phase ORDER BY CASE phase WHEN 'PP' THEN 1 WHEN 'MID' THEN 2 ELSE 3 END""")
    bt = backtest_results()
    validation = next((m for m in matches if m["is_validation_case"]), None)
    validation_detail = None
    if validation and bt["run"]:
        try:
            validation_detail = backtest_match(int(validation["match_id"]))
        except LookupError:
            validation_detail = None
    params = active_params().as_dict()
    top = fetch_all("""SELECT player_id, player_name, SUM(runs) AS runs, SUM(balls_faced) AS balls,
                              ROUND(100.0*SUM(runs)/NULLIF(SUM(balls_faced),0),1) AS sr
                       FROM v_rcb_player_season GROUP BY player_id, player_name ORDER BY runs DESC LIMIT 5""")
    return clean({
        "season": {"played": len(done), "wins": wins, "losses": len(done) - wins,
                   "avg_score": round(sum(m["rcb_runs"] for m in done) / len(done), 1) if done else None,
                   "highest": max((m["rcb_runs"] for m in done), default=None),
                   "points": wins * 2},
        "matches": matches, "phase_averages": phase_avg, "opponent_phase_averages": opp_phase_avg,
        "backtest": {"run": bt["run"], "summary": bt["summary"], "matches": bt["matches"]},
        "validation": validation_detail, "active_params": params, "top_batters": top,
    })


# ---------------------------------------------------------------------- analytics
def phase_analytics() -> dict:
    rows = fetch_all("""SELECT s.match_id, m.rcb_match_no, m.opponent_code, s.batting_side, s.phase, s.phase_runs,
                               s.phase_wickets, s.phase_balls, s.phase_run_rate
                        FROM v_phase_innings_summary s JOIN v_rcb_match_summary m ON m.match_id = s.match_id
                        ORDER BY m.match_date, s.batting_side,
                                 CASE s.phase WHEN 'PP' THEN 1 WHEN 'MID' THEN 2 ELSE 3 END""")
    dist = fetch_all("""SELECT phase,
                               SUM(CASE WHEN runs_batter = 0 AND is_legal AND NOT is_wicket THEN 1 ELSE 0 END) AS dots,
                               SUM(CASE WHEN runs_batter IN (1,2,3) THEN 1 ELSE 0 END) AS rotations,
                               SUM(CASE WHEN runs_batter = 4 THEN 1 ELSE 0 END) AS fours,
                               SUM(CASE WHEN runs_batter = 6 THEN 1 ELSE 0 END) AS sixes,
                               SUM(CASE WHEN is_wicket THEN 1 ELSE 0 END) AS wickets,
                               SUM(CASE WHEN is_legal THEN 1 ELSE 0 END) AS balls
                        FROM rcb_ball_by_ball b JOIN rcb_innings i ON i.innings_id = b.innings_id
                        WHERE i.batting_side = 'RCB' GROUP BY phase
                        ORDER BY CASE phase WHEN 'PP' THEN 1 WHEN 'MID' THEN 2 ELSE 3 END""")
    return clean({"innings_phases": rows, "outcome_distribution": dist})


def venue_analytics() -> dict:
    rows = fetch_all("""SELECT v.venue_id, v.venue_code, v.venue_name, v.city, v.prior_pp_runs, v.prior_mid_runs,
                               v.prior_death_runs, v.prior_first_inn_total,
                               COUNT(DISTINCT m.match_id) AS matches,
                               ROUND(AVG(s.phase_runs) FILTER (WHERE s.phase='PP' AND s.phase_balls=36),2)  AS obs_pp,
                               ROUND(AVG(s.phase_runs) FILTER (WHERE s.phase='MID' AND s.phase_balls=60),2) AS obs_mid,
                               ROUND(AVG(s.phase_runs) FILTER (WHERE s.phase='DEATH' AND s.phase_balls=24),2) AS obs_death
                        FROM venues v
                        LEFT JOIN rcb_matches m ON m.venue_id = v.venue_id
                        LEFT JOIN v_phase_innings_summary s ON s.match_id = m.match_id
                        GROUP BY v.venue_id ORDER BY v.venue_id""")
    firsts = fetch_all("""SELECT m.venue_id, ROUND(AVG(i.total_runs),1) AS avg_first_innings
                          FROM rcb_innings i JOIN rcb_matches m ON m.match_id = i.match_id
                          WHERE i.innings_no = 1 GROUP BY m.venue_id""")
    fmap = {f["venue_id"]: f["avg_first_innings"] for f in firsts}
    for r in rows:
        r["obs_first_innings"] = fmap.get(r["venue_id"])
    opp = fetch_all("""SELECT t.team_code, t.team_name, t.primary_color, s.phase,
                              ROUND(6.0*SUM(s.phase_runs)/NULLIF(SUM(s.phase_balls),0),2) AS econ_vs_rcb,
                              SUM(s.phase_wickets) AS wickets, SUM(s.phase_balls) AS balls
                       FROM v_phase_innings_summary s JOIN opponent_teams t ON t.team_code = s.bowling_team
                       WHERE s.batting_side = 'RCB' GROUP BY t.team_code, t.team_name, t.primary_color, s.phase
                       ORDER BY t.team_code, CASE s.phase WHEN 'PP' THEN 1 WHEN 'MID' THEN 2 ELSE 3 END""")
    return clean({"venues": rows, "opponent_bowling": opp})


def player_analytics() -> dict:
    batting = fetch_all("""SELECT * FROM v_rcb_player_season
                           ORDER BY player_id, CASE phase WHEN 'PP' THEN 1 WHEN 'MID' THEN 2 ELSE 3 END""")
    bowling = fetch_all("""SELECT * FROM v_rcb_bowling_season
                           ORDER BY player_id, CASE phase WHEN 'PP' THEN 1 WHEN 'MID' THEN 2 ELSE 3 END""")
    contrib = fetch_all("""SELECT p.player_id, p.short_name, SUM(b.runs_batter) AS runs,
                                  ROUND(100.0*SUM(b.runs_batter)/NULLIF((SELECT SUM(runs_batter) FROM rcb_ball_by_ball
                                        WHERE batter_rcb_id IS NOT NULL),0),2) AS share_pct
                           FROM rcb_ball_by_ball b JOIN rcb_players p ON p.player_id = b.batter_rcb_id
                           GROUP BY p.player_id, p.short_name ORDER BY runs DESC""")
    return clean({"batting": batting, "bowling": bowling, "contribution": contrib})
