"""End-to-end prediction for one RCB match using only pre-match information.

Steps: player profiles -> XI capacity -> venue/opponent adjustment ->
target recommendation -> DP checkpoint plan + capacity projection.
"""
import pandas as pd

from backend.formulas import PHASES, adjusted_capacity, bowling_strength_index
from backend.engine.opponent_adjustment_engine import (compute_opponent_profile, league_economy,
                                                       rcb_bowling_economy)
from backend.engine.player_profile_engine import build_player_profiles
from backend.engine.season_data import EngineParams, SeasonData
from backend.engine.target_solver import projection, recommend_target, solve_checkpoints
from backend.engine.team_capacity_engine import compute_team_capacity
from backend.engine.venue_adjustment_engine import compute_venue_profile


def predict_match(data: SeasonData, match_id: int, params: EngineParams, *, xi_player_ids: list[int] | None = None,
                  plan_mode: str | None = None, chase_target: float | None = None,
                  wicket_penalty: float | None = None) -> dict:
    match = data.match(match_id)

    # Playing XI: fixture selection or a user-supplied XI (batting order = list order)
    if xi_player_ids:
        if len(xi_player_ids) != 11 or len(set(xi_player_ids)) != 11:
            raise ValueError("A playing XI must contain exactly 11 distinct players")
        known = set(data.players["player_id"].astype(int))
        unknown = [p for p in xi_player_ids if int(p) not in known]
        if unknown:
            raise ValueError(f"Unknown player ids in XI: {unknown}")
        overseas = sum(bool(data.player(int(p))["is_overseas"]) for p in xi_player_ids)
        if overseas > 4:
            raise ValueError(f"A playing XI may include at most 4 overseas players (got {overseas})")
        xi = pd.DataFrame({"player_id": xi_player_ids, "batting_order": range(1, 12)})
        custom = True
    else:
        xi = data.xi_for_match(match_id)
        custom = False
    impact = data.impact_for_match(match_id)

    history = data.history_before(match_id)
    profiles = build_player_profiles(data, match_id, xi, params)
    profiles, capacity = compute_team_capacity(profiles, history)

    venue = compute_venue_profile(data, match_id)
    l_econ = league_economy(data, match_id)
    opp = compute_opponent_profile(data, match_id, l_econ)
    vf = {p["phase"]: p["venue_factor"] for p in venue["phases"]}
    shares = {p["phase"]: p["phase_share"] for p in venue["phases"]}
    threat = {p["phase"]: p["opp_threat"] for p in opp["phases"]}

    adj_runs, adj_wkts = {}, {}
    cap_rows = []
    for _, c in capacity.iterrows():
        p = c["phase"]
        r, w = adjusted_capacity(c["raw_runs"], c["raw_wickets"], vf[p], threat[p], params.opp_alpha, params.venue_beta)
        adj_runs[p], adj_wkts[p] = r, w
        cap_rows.append({**c.to_dict(), "venue_factor": vf[p], "opp_threat": threat[p],
                         "adj_runs": round(r, 2), "adj_wickets": round(w, 3)})
    capacity_total = sum(adj_runs.values())
    capacity_wkts = min(10.0, sum(adj_wkts.values()))

    # Bowling strength index (formula 15) from the XI + impact bowlers
    bowler_ids = [int(x) for x in list(xi["player_id"]) + impact
                  if any(pd.notna(data.player(int(x))[f"prior_econ_{ph}"]) for ph in ("pp", "mid", "death"))]
    rcb_econ = rcb_bowling_economy(data, match_id, bowler_ids)
    league_overall = sum(l_econ[p] * n for p, n in (("PP", 6), ("MID", 10), ("DEATH", 4))) / 20
    bsi = bowling_strength_index(league_overall, rcb_econ)
    target = recommend_target(venue["venue_par"], capacity_total, bsi, params.target_lambda)

    mode = plan_mode or ("BAT_FIRST" if bool(match["rcb_batting_first"]) else "CHASE")
    if mode == "CHASE":
        if chase_target is None:
            if match["status"] == "COMPLETED" and pd.notna(match.get("opp_runs")):
                chase_target = float(match["opp_runs"]) + 1      # known at the innings break
            else:
                chase_target = target["t_recommended"]
        plan_target = float(chase_target)
    else:
        plan_target = target["t_recommended"]

    w_pen = params.wicket_penalty if wicket_penalty is None else float(wicket_penalty)
    plan = solve_checkpoints(adj_runs, adj_wkts, plan_target, shares, w_pen)
    proj = projection(adj_runs, adj_wkts)

    return {
        "match_id": int(match_id), "rcb_match_no": int(match["rcb_match_no"]), "ipl_match_no": int(match["ipl_match_no"]),
        "match_date": str(pd.Timestamp(match["match_date"]).date()), "plan_mode": mode, "custom_xi": custom,
        "history_matches": len(data.history_match_ids(match_id)),
        "history_cutoff": str(pd.Timestamp(match["match_date"]).date()),
        "params": {**params.as_dict(), "wicket_penalty": w_pen},
        "player_profiles": profiles.to_dict(orient="records"),
        "capacity": cap_rows, "capacity_total": round(capacity_total, 2), "capacity_wickets": round(capacity_wkts, 2),
        "venue": venue, "opponent": opp, "league_econ": {k: round(v, 3) for k, v in l_econ.items()},
        "rcb_bowling_econ": round(rcb_econ, 3), "bowler_ids": bowler_ids,
        "target": target, "plan_target": round(plan_target, 2), "plan": plan, "projection": proj,
        "impact_player_ids": impact,
    }
