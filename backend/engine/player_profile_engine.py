"""Player phase profiles: recency-weighted SR, OutProb and expected balls.

The weighted sums are computed in one vectorised pass; the per-player
values are exactly formulas 03 and 04 (see backend/formulas).

Formulas 02 (recency), 03 (SR), 04 (OutProb), 05 (cold-start shrinkage)
and 06 (expected balls per innings).
"""
import pandas as pd

from backend.formulas import PHASES, expected_phase_balls, prior_balls, shrink_to_prior
from backend.engine.recency_engine import apply_recency, match_weights
from backend.engine.season_data import EngineParams, SeasonData

K_MATCHES = 2.0   # pseudo-matches of the batting-slot template in formula 06


def build_player_profiles(data: SeasonData, match_id: int, xi: pd.DataFrame, params: EngineParams) -> pd.DataFrame:
    """One row per (player in XI, phase).

    xi: DataFrame[player_id, batting_order] for the batting XI of the target match.
    """
    history = data.history_before(match_id)
    rcb_bat = history[(history["batting_side"] == "RCB") & history["is_legal"]]
    rcb_bat = apply_recency(rcb_bat, params.half_life_days)
    mweights = match_weights(history, params.half_life_days)

    hist_ids = set(data.history_match_ids(match_id))
    sel = data.selections[data.selections["match_id"].isin(hist_ids) & data.selections["batting_order"].notna()]

    # vectorised weighted sums per (player, phase)  -> formulas 03/04 inputs
    rb = rcb_bat.assign(wr=rcb_bat["w"] * rcb_bat["runs_batter"], wo=rcb_bat["w"] * rcb_bat["is_wicket"].astype(float))
    agg = rb.groupby(["batter_rcb_id", "phase"]).agg(raw=("w", "size"), sw=("w", "sum"), swr=("wr", "sum"),
                                                    swo=("wo", "sum")).to_dict(orient="index")
    bpm = rb.groupby(["match_id", "batter_rcb_id", "phase"]).size().to_dict()
    played_by = sel.groupby("player_id")["match_id"].apply(lambda s: [int(x) for x in s]).to_dict()
    batted = set(int(x) for x in rb["batter_rcb_id"].unique())

    rows = []
    for pid, order in zip(xi["player_id"].astype(int), xi["batting_order"].astype(int)):
        p = data.player(pid)
        played = played_by.get(pid, [])
        for phase in PHASES:
            a = agg.get((pid, phase), {"raw": 0, "sw": 0.0, "swr": 0.0, "swo": 0.0})
            sw = float(a["sw"])
            prior_sr = float(p[f"prior_sr_{phase.lower()}"])
            prior_out = float(p[f"prior_out_{phase.lower()}"])
            sr_obs = 100.0 * a["swr"] / sw if sw > 0 else None          # formula 03
            out_obs = a["swo"] / sw if sw > 0 else None                  # formula 04
            sr = 100.0 * shrink_to_prior(float(a["swr"]), sw, prior_sr / 100.0, params.shrinkage_k)
            out = shrink_to_prior(float(a["swo"]), sw, prior_out, params.shrinkage_k)
            balls_list = [float(bpm.get((m, pid, phase), 0)) for m in played]
            w_list = [mweights.get(m, 0.0) for m in played]
            exp_b = expected_phase_balls(balls_list, w_list, prior_balls(order, phase), K_MATCHES)
            rows.append({
                "player_id": pid, "player_name": p["player_name"], "short_name": p["short_name"],
                "role": p["role"], "batting_order": order, "phase": phase,
                "raw_balls": int(a["raw"]), "weighted_balls": round(sw, 3),
                "sr_observed": None if sr_obs is None else round(float(sr_obs), 2),
                "out_observed": None if out_obs is None else round(float(out_obs), 4),
                "prior_sr": prior_sr, "prior_out": prior_out,
                "sr": round(sr, 2), "out_prob": round(out, 4), "exp_balls": round(exp_b, 3),
                "appearances": len(played), "cold_start": pid not in batted,
            })
    return pd.DataFrame(rows)
