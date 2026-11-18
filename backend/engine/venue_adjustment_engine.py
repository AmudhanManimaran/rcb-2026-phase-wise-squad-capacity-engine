"""Venue phase profile: blended averages, phase shares and venue factors.

Formulas 11 (venue phase share) and 12 (venue factor with shrinkage).
"""
import numpy as np

from backend.formulas import PHASE_BALLS, PHASES, blended_average, venue_phase_factor, venue_phase_share
from backend.engine.season_data import SeasonData

K_VENUE = 3.0     # pseudo-innings for venue prior
K_LEAGUE = 6.0    # pseudo-innings for league prior


def compute_venue_profile(data: SeasonData, match_id: int) -> dict:
    m = data.match(match_id)
    venue = data.venue(int(m["venue_id"]))
    hist_ids = set(data.history_match_ids(match_id))
    pt = data.innings_phase_table()
    pt = pt[pt["match_id"].isin(hist_ids)].merge(data.matches[["match_id", "venue_id"]], on="match_id")

    league_prior = {p: float(data.venues[f"prior_{p.lower()}_runs"].mean()) for p in PHASES}
    phases = []
    for phase in PHASES:
        full = pt[(pt["phase"] == phase) & (pt["balls"] >= PHASE_BALLS[phase])]
        at_venue = full[full["venue_id"] == venue["venue_id"]]
        n_v = len(at_venue)
        obs_v = float(at_venue["runs"].mean()) if n_v else None
        v_avg = blended_average(obs_v, n_v, float(venue[f"prior_{phase.lower()}_runs"]), K_VENUE)
        l_avg = blended_average(float(full["runs"].mean()) if len(full) else None, len(full), league_prior[phase], K_LEAGUE)
        phases.append({"phase": phase, "sample_innings": n_v, "observed_avg": None if obs_v is None else round(obs_v, 2),
                       "venue_avg": round(v_avg, 2), "league_avg": round(l_avg, 2),
                       "venue_factor": round(venue_phase_factor(v_avg, l_avg), 4)})
    shares = venue_phase_share({p["phase"]: p["venue_avg"] for p in phases})
    for p in phases:
        p["phase_share"] = round(shares[p["phase"]], 4)

    # venue par: first-innings totals at the venue (all sides) blended with the prior
    inn = data.innings[(data.innings["match_id"].isin(hist_ids)) & (data.innings["innings_no"] == 1)]
    inn = inn.merge(data.matches[["match_id", "venue_id"]], on="match_id")
    firsts = inn.loc[inn["venue_id"] == venue["venue_id"], "total_runs"].astype(float)
    par = blended_average(float(firsts.mean()) if len(firsts) else None, len(firsts),
                          float(venue["prior_first_inn_total"]), K_VENUE)
    return {"venue_id": int(venue["venue_id"]), "venue_code": venue["venue_code"], "venue_name": venue["venue_name"],
            "phases": phases, "venue_par": round(par, 2), "par_sample": int(len(firsts))}
