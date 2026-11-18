"""Squad phase capacity: ball shares, team SR/OutProb and raw capacity.

Formulas 07 (ball share), 08 (team SR), 09 (team OutProb), 10 (capacity).
"""
import pandas as pd

from backend.formulas import PHASE_BALLS, PHASES, ball_share, phase_capacity, team_out_probability, team_strike_rate

EXTRAS_PRIOR = 0.055      # extras per legal ball (prior)
EXTRAS_K = 240            # pseudo-balls


def extras_rate(history: pd.DataFrame) -> float:
    legal = float(history["is_legal"].sum()) if len(history) else 0.0
    extras = float(history["runs_extras"].sum()) if len(history) else 0.0
    return (extras + EXTRAS_K * EXTRAS_PRIOR) / (legal + EXTRAS_K)


def compute_team_capacity(profiles: pd.DataFrame, history: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Returns (profiles with ball_share, capacity per phase)."""
    profiles = profiles.copy()
    share_map = {}
    xr = extras_rate(history)
    caps = []
    for phase in PHASES:
        sub = profiles[profiles["phase"] == phase]
        shares = ball_share(dict(zip(sub["player_id"], sub["exp_balls"])))
        srs = dict(zip(sub["player_id"], sub["sr"]))
        outs = dict(zip(sub["player_id"], sub["out_prob"]))
        tsr = team_strike_rate(shares, srs)
        tout = team_out_probability(shares, outs)
        runs, wkts = phase_capacity(tsr, tout, PHASE_BALLS[phase], xr)
        share_map.update({(pid, phase): round(s, 4) for pid, s in shares.items()})
        caps.append({"phase": phase, "phase_balls": PHASE_BALLS[phase], "team_sr": round(tsr, 2),
                     "team_out_prob": round(tout, 4), "extras_rate": round(xr, 4),
                     "raw_runs": round(runs, 2), "raw_wickets": round(wkts, 3)})
    profiles["ball_share"] = [share_map[(pid, ph)] for pid, ph in zip(profiles["player_id"], profiles["phase"])]
    return profiles, pd.DataFrame(caps)
