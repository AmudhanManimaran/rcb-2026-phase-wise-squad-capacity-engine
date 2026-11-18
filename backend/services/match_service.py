"""Fixtures, results and match detail."""
from backend.database import fetch_all, fetch_one
from backend.services.common import clean


def list_matches() -> list[dict]:
    return clean(fetch_all("SELECT * FROM v_rcb_match_summary ORDER BY match_date"))


def match_detail(match_id: int) -> dict:
    m = fetch_one("SELECT * FROM v_rcb_match_summary WHERE match_id = %s", (match_id,))
    if not m:
        raise LookupError(f"Match {match_id} not found")
    innings = fetch_all("SELECT * FROM rcb_innings WHERE match_id = %s ORDER BY innings_no", (match_id,))
    xi = fetch_all("""SELECT s.player_id, s.batting_order, s.is_impact_player, p.player_name, p.short_name, p.role,
                             p.is_overseas, p.is_captain
                      FROM rcb_squad_selections s JOIN rcb_players p ON p.player_id = s.player_id
                      WHERE s.match_id = %s ORDER BY s.batting_order NULLS LAST""", (match_id,))
    rcb_bat = fetch_all("""SELECT p.short_name AS name, s.batting_order,
                                  SUM(b.runs_batter) AS runs, SUM(CASE WHEN b.is_legal THEN 1 ELSE 0 END) AS balls,
                                  SUM(CASE WHEN b.runs_batter=4 THEN 1 ELSE 0 END) AS fours,
                                  SUM(CASE WHEN b.runs_batter=6 THEN 1 ELSE 0 END) AS sixes,
                                  BOOL_OR(b.is_wicket) AS out
                           FROM rcb_ball_by_ball b JOIN rcb_players p ON p.player_id = b.batter_rcb_id
                           JOIN rcb_squad_selections s ON s.match_id = b.match_id AND s.player_id = b.batter_rcb_id
                           WHERE b.match_id = %s GROUP BY p.short_name, s.batting_order ORDER BY s.batting_order""",
                        (match_id,))
    rcb_bowl = fetch_all("""SELECT p.short_name AS name, SUM(CASE WHEN b.is_legal THEN 1 ELSE 0 END) AS balls,
                                   SUM(b.runs_batter + CASE WHEN b.extra_type='WIDE' THEN b.runs_extras ELSE 0 END) AS runs,
                                   SUM(CASE WHEN b.is_wicket THEN 1 ELSE 0 END) AS wickets
                            FROM rcb_ball_by_ball b JOIN rcb_players p ON p.player_id = b.bowler_rcb_id
                            WHERE b.match_id = %s GROUP BY p.short_name ORDER BY wickets DESC, runs""", (match_id,))
    overs = fetch_all("""SELECT i.batting_side, b.over_no, SUM(b.runs_batter + b.runs_extras) AS runs,
                                SUM(CASE WHEN b.is_wicket THEN 1 ELSE 0 END) AS wickets
                         FROM rcb_ball_by_ball b JOIN rcb_innings i ON i.innings_id = b.innings_id
                         WHERE b.match_id = %s GROUP BY i.batting_side, b.over_no ORDER BY i.batting_side, b.over_no""",
                      (match_id,))
    worm = {"RCB": [], "OPP": []}
    acc = {"RCB": 0, "OPP": 0}
    for o in overs:
        acc[o["batting_side"]] += int(o["runs"])
        worm[o["batting_side"]].append({"over": int(o["over_no"]), "runs": int(o["runs"]), "cum": acc[o["batting_side"]],
                                        "wickets": int(o["wickets"])})
    return clean({"match": m, "innings": innings, "selection": xi, "rcb_batting": rcb_bat, "rcb_bowling": rcb_bowl,
                  "worm": worm})
