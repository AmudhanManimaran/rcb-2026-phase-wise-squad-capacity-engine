"""Opponent bowling threat (formula 13) and RCB bowling strength (formula 15 input)."""
import numpy as np

from backend.formulas import PHASES, opponent_threat
from backend.engine.season_data import SeasonData

K_OPP_BALLS = 36.0       # pseudo-balls of the scouting prior per phase
K_LEAGUE_BALLS = 180.0
K_RCB_BOWL_BALLS = 120.0


def _league_prior_econ(data: SeasonData) -> dict:
    overs = {"PP": 6, "MID": 10, "DEATH": 4}
    return {p: float(data.venues[f"prior_{p.lower()}_runs"].mean()) / overs[p] for p in PHASES}


def league_economy(data: SeasonData, match_id: int) -> dict:
    h = data.history_before(match_id)
    prior = _league_prior_econ(data)
    out = {}
    for p in PHASES:
        hp = h[h["phase"] == p]
        balls = float(hp["is_legal"].sum())
        runs = float(hp["runs_total"].sum())
        out[p] = (runs + K_LEAGUE_BALLS / 6 * prior[p]) / (balls + K_LEAGUE_BALLS) * 6
    return out


def compute_opponent_profile(data: SeasonData, match_id: int, league_econ: dict) -> dict:
    m = data.match(match_id)
    team = data.team(int(m["opponent_id"]))
    h = data.history_before(match_id)
    vs = h[(h["batting_side"] == "RCB") & (h["bowling_team"] == team["team_code"])]
    phases = []
    for p in PHASES:
        prior_econ = league_econ[p] / float(team[f"bowl_{p.lower()}"])
        hp = vs[vs["phase"] == p]
        balls = float(hp["is_legal"].sum())
        econ = (float(hp["runs_total"].sum()) + K_OPP_BALLS / 6 * prior_econ) / (balls + K_OPP_BALLS) * 6
        phases.append({"phase": p, "sample_overs": round(balls / 6, 1), "opp_econ": round(econ, 3),
                       "league_econ": round(league_econ[p], 3), "opp_threat": round(opponent_threat(econ, league_econ[p]), 4)})
    return {"opponent_id": int(team["team_id"]), "team_code": team["team_code"], "team_name": team["team_name"],
            "phases": phases}


def rcb_bowling_economy(data: SeasonData, match_id: int, bowler_ids: list[int]) -> float:
    """Shrunk overall economy of the RCB attack for the match (XI + impact bowlers)."""
    priors = []
    for pid in bowler_ids:
        p = data.player(pid)
        vals = [p[f"prior_econ_{x}"] for x in ("pp", "mid", "death") if p[f"prior_econ_{x}"] is not None
                and not (isinstance(p[f"prior_econ_{x}"], float) and np.isnan(p[f"prior_econ_{x}"]))]
        if vals:
            priors.append(float(np.mean(vals)))
    prior = float(np.mean(priors)) if priors else 9.5
    h = data.history_before(match_id)
    rb = h[h["bowler_rcb_id"].isin(bowler_ids)]
    balls = float(rb["is_legal"].sum())
    return (float(rb["runs_total"].sum()) + K_RCB_BOWL_BALLS / 6 * prior) / (balls + K_RCB_BOWL_BALLS) * 6
