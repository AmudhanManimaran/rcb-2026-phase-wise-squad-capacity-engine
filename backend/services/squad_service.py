"""RCB squad intelligence: player list, phase profiles and form."""
import pandas as pd

from backend.database import fetch_all, fetch_one
from backend.engine.player_profile_engine import build_player_profiles
from backend.services.common import active_params, clean, season_data


def _default_as_of(data) -> int:
    v = data.matches[data.matches["is_validation_case"]]
    return int(v.iloc[0]["match_id"]) if len(v) else int(data.matches["match_id"].max())


def list_squad(as_of_match_id: int | None = None) -> dict:
    data = season_data()
    mid = as_of_match_id or _default_as_of(data)
    params = active_params()
    everyone = pd.DataFrame({"player_id": data.players["player_id"].astype(int),
                             "batting_order": data.players["preferred_slot"].astype(int)})
    prof = build_player_profiles(data, mid, everyone, params)
    bat = fetch_all("""SELECT player_id, SUM(runs) AS runs, SUM(balls_faced) AS balls, SUM(dismissals) AS outs,
                              SUM(fours) AS fours, SUM(sixes) AS sixes FROM v_rcb_player_season GROUP BY player_id""")
    bowl = fetch_all("""SELECT player_id, SUM(legal_balls) AS balls, SUM(runs_conceded) AS runs, SUM(wickets) AS wkts
                        FROM v_rcb_bowling_season GROUP BY player_id""")
    sel = fetch_all("""SELECT player_id, COUNT(*) FILTER (WHERE batting_order IS NOT NULL) AS xi_count,
                              COUNT(*) FILTER (WHERE is_impact_player) AS impact_count
                       FROM rcb_squad_selections GROUP BY player_id""")
    bmap, wmap, smap = ({r["player_id"]: r for r in x} for x in (bat, bowl, sel))
    xi_next = set(data.xi_for_match(mid)["player_id"].tolist())
    players = []
    for p in data.players.to_dict(orient="records"):
        pid = int(p["player_id"])
        b, w, s = bmap.get(pid, {}), wmap.get(pid, {}), smap.get(pid, {})
        phases = {r["phase"]: {k: r[k] for k in ("sr", "out_prob", "sr_observed", "raw_balls", "weighted_balls", "prior_sr")}
                  for r in prof[prof["player_id"] == pid].to_dict(orient="records")}
        runs, balls, outs = b.get("runs") or 0, b.get("balls") or 0, b.get("outs") or 0
        players.append({
            **{k: p[k] for k in ("player_id", "player_name", "short_name", "role", "batting_style", "bowling_style",
                                 "is_overseas", "is_captain", "preferred_slot", "is_synthetic_profile")},
            "matches": int(s.get("xi_count") or 0), "impact_apps": int(s.get("impact_count") or 0),
            "runs": int(runs), "balls": int(balls), "strike_rate": round(100 * runs / balls, 1) if balls else None,
            "average": round(runs / outs, 1) if outs else None, "fours": int(b.get("fours") or 0),
            "sixes": int(b.get("sixes") or 0), "wickets": int(w.get("wkts") or 0),
            "economy": round(6 * w["runs"] / w["balls"], 2) if w.get("balls") else None,
            "overs": f"{int(w['balls']) // 6}.{int(w['balls']) % 6}" if w.get("balls") else None,
            "in_xi_for_match": pid in xi_next, "cold_start": bool(prof[prof["player_id"] == pid]["cold_start"].iloc[0]),
            "phases": phases,
        })
    m = data.match(mid)
    return clean({"as_of_match_id": mid, "as_of_rcb_match_no": int(m["rcb_match_no"]),
                  "half_life_days": params.half_life_days, "players": players})


def player_detail(player_id: int) -> dict:
    data = season_data()
    p = fetch_one("SELECT * FROM rcb_players WHERE player_id = %s", (player_id,))
    if not p:
        raise LookupError(f"Player {player_id} not found")
    params = active_params()
    form = []
    for mid in data.matches.sort_values("match_date")["match_id"].astype(int):
        prof = build_player_profiles(data, mid, pd.DataFrame({"player_id": [player_id],
                                                              "batting_order": [int(p["preferred_slot"])]}), params)
        row = {"match_id": mid, "rcb_match_no": int(data.match(mid)["rcb_match_no"])}
        for r in prof.to_dict(orient="records"):
            row[f"sr_{r['phase'].lower()}"] = r["sr"]
            row[f"out_{r['phase'].lower()}"] = r["out_prob"]
        form.append(row)
    innings = fetch_all("""SELECT m.match_id, m.rcb_match_no, m.opponent_code, m.match_date, s.batting_order, s.is_impact_player,
                                  COALESCE(SUM(b.runs_batter),0) AS runs,
                                  COALESCE(SUM(CASE WHEN b.is_legal THEN 1 ELSE 0 END),0) AS balls,
                                  COALESCE(BOOL_OR(b.is_wicket), FALSE) AS dismissed
                           FROM rcb_squad_selections s
                           JOIN v_rcb_match_summary m ON m.match_id = s.match_id
                           LEFT JOIN rcb_ball_by_ball b ON b.match_id = s.match_id AND b.batter_rcb_id = s.player_id
                           WHERE s.player_id = %s
                           GROUP BY m.match_id, m.rcb_match_no, m.opponent_code, m.match_date, s.batting_order, s.is_impact_player
                           ORDER BY m.match_date""", (player_id,))
    bowling = fetch_all("""SELECT m.rcb_match_no, m.opponent_code, SUM(CASE WHEN b.is_legal THEN 1 ELSE 0 END) AS balls,
                                  SUM(b.runs_batter + CASE WHEN b.extra_type='WIDE' THEN b.runs_extras ELSE 0 END) AS runs,
                                  SUM(CASE WHEN b.is_wicket THEN 1 ELSE 0 END) AS wickets
                           FROM rcb_ball_by_ball b JOIN v_rcb_match_summary m ON m.match_id = b.match_id
                           WHERE b.bowler_rcb_id = %s GROUP BY m.rcb_match_no, m.opponent_code, m.match_date
                           ORDER BY m.match_date""", (player_id,))
    phase_stats = fetch_all("""SELECT * FROM v_rcb_player_season WHERE player_id = %s
                               ORDER BY CASE phase WHEN 'PP' THEN 1 WHEN 'MID' THEN 2 ELSE 3 END""", (player_id,))
    bowl_stats = fetch_all("""SELECT * FROM v_rcb_bowling_season WHERE player_id = %s
                              ORDER BY CASE phase WHEN 'PP' THEN 1 WHEN 'MID' THEN 2 ELSE 3 END""", (player_id,))
    return clean({"player": p, "form": form, "innings": innings, "bowling_spells": bowling,
                  "phase_stats": phase_stats, "bowling_phase_stats": bowl_stats,
                  "half_life_days": params.half_life_days})
