"""Synthetic IPL 2026 RCB season generator: fixtures, XIs, tosses and both innings."""
from datetime import date, timedelta

import numpy as np

from backend.generator.innings_generator import simulate_innings
from backend.generator.player_generator import (LEAGUE_ECON, OPP_BASE_OUT, OPP_SLOT_PROFILE,
                                                rcb_season_abilities)

SEASON_START = date(2026, 3, 28)
# (ipl_match_no, day offset from season start, opponent code, home?)
FIXTURES = [
    (1, 0, "KKR", True), (6, 4, "CSK", False), (11, 8, "MI", True), (16, 12, "DC", False),
    (21, 16, "SRH", True), (26, 20, "GT", False), (31, 24, "RR", True), (37, 28, "LSG", False),
    (42, 33, "PBKS", True), (47, 37, "KKR", False), (52, 41, "CSK", True), (57, 45, "MI", False),
    (62, 50, "DC", True), (67, 55, "SRH", False),
]
VALIDATION_IPL_MATCH = 67

# Player ids (see database/seed/01_rcb_squad.sql)
SALT, KOHLI, PADIKKAL, PATIDAR, VIYER, JITESH, TDAVID, KRUNAL, SHEPHERD, BHUVI, HAZLEWOOD = range(1, 12)
DAYAL, SUYASH, RASIKH, BETHELL, SWAPNIL, THUSHARA, ABHINANDAN, MYADAV, DUFFY = 12, 13, 14, 15, 16, 17, 18, 19, 20
COX = 22
BASE_XI = [SALT, KOHLI, PADIKKAL, PATIDAR, VIYER, JITESH, TDAVID, KRUNAL, SHEPHERD, BHUVI, HAZLEWOOD]


def rcb_selection(rcb_match_no: int) -> tuple[list[int], int]:
    """Batting XI (in order) and the bowling impact player for an RCB match."""
    xi = list(BASE_XI)
    impact = DAYAL
    if rcb_match_no in (3, 4):            # Bethell at 3, Mangesh Yadav for Shepherd
        xi[2] = BETHELL
        xi[8] = MYADAV
    if rcb_match_no in (6, 7):            # Hazlewood rested
        xi[10] = DUFFY
    if rcb_match_no == 9:                 # Jitesh unavailable: Cox keeps, Swapnil for Shepherd
        xi[5] = COX
        xi[8] = SWAPNIL
    if rcb_match_no == 8:
        impact = RASIKH
    if rcb_match_no == 11:
        impact = SUYASH
    if rcb_match_no == 12:
        xi[9] = RASIKH
        impact = DAYAL
    return xi, impact


def _plural(n: int, word: str) -> str:
    return f"{n} {word}" + ("" if n == 1 else "s")


def _venue_mult(venue: dict, league_prior: dict) -> dict:
    return {"PP": venue["prior_pp_runs"] / league_prior["PP"],
            "MID": venue["prior_mid_runs"] / league_prior["MID"],
            "DEATH": venue["prior_death_runs"] / league_prior["DEATH"]}


def generate_season(players: list[dict], teams: list[dict], venues: list[dict], opp_players: list[dict],
                    seed: int = 2026) -> dict:
    rng = np.random.default_rng(seed)
    pmap = {p["player_id"]: p for p in players}
    tmap = {t["team_code"]: t for t in teams}
    vmap = {v["venue_id"]: v for v in venues}
    league_prior = {ph: float(np.mean([v[f"prior_{ph.lower()}_runs"] for v in venues])) for ph in ("PP", "MID", "DEATH")}
    abilities = rcb_season_abilities(players, len(FIXTURES), rng)

    matches, innings_rows, deliveries, selections = [], [], [], []

    for idx, (ipl_no, offset, opp_code, home) in enumerate(FIXTURES):
        match_id = idx + 1
        opp = tmap[opp_code]
        venue = vmap[1] if home else vmap[opp["home_venue_id"]]
        vm = _venue_mult(venue, league_prior)
        day = float(np.exp(rng.normal(0, 0.045)))         # pitch/conditions of the day
        xi, impact = rcb_selection(match_id)

        for order, pid in enumerate(xi, start=1):
            selections.append({"match_id": match_id, "player_id": pid, "batting_order": order,
                               "is_playing_xi": True, "is_impact_player": False})
        selections.append({"match_id": match_id, "player_id": impact, "batting_order": None,
                           "is_playing_xi": False, "is_impact_player": True})

        # RCB batting lineup (true abilities, never visible to the engine)
        rcb_lineup = []
        for pid in xi:
            p, ab = pmap[pid], abilities[pid]
            form = float(np.exp(ab["form"][idx]))
            rcb_lineup.append({
                "id": pid,
                "mu": {ph: p[f"prior_sr_{ph.lower()}"] / 100 * ab["talent_sr"] * form * vm[ph] * day
                       for ph in ("PP", "MID", "DEATH")},
                "q": {ph: p[f"prior_out_{ph.lower()}"] * ab["talent_out"] / form for ph in ("PP", "MID", "DEATH")},
            })
        # RCB bowlers: XI + impact with bowling priors (impact replaces the No.3 batter in the field)
        rcb_bowlers = []
        for pid in [x for x in xi if x != xi[2]] + [impact]:
            p = pmap[pid]
            if any(p[f"prior_econ_{ph}"] is not None for ph in ("pp", "mid", "death")):
                f = float(np.exp(abilities[pid]["form"][idx] * 0.6))
                rcb_bowlers.append({"id": pid, "econ": {
                    ph: (p[f"prior_econ_{ph.lower()}"] / f if p[f"prior_econ_{ph.lower()}"] is not None else None)
                    for ph in ("PP", "MID", "DEATH")}})

        # Opponent lineup and bowlers
        team_players = sorted([o for o in opp_players if o["team_id"] == opp["team_id"]], key=lambda o: o["slot"])
        opp_lineup = []
        for o in team_players:
            sr = OPP_SLOT_PROFILE[o["slot"]]
            opp_lineup.append({
                "id": o["opp_player_id"],
                "mu": {ph: sr[i] / 100 * o["bat_sr_factor"] * opp["bat_strength"] * vm[ph] * day
                       for i, ph in enumerate(("PP", "MID", "DEATH"))},
                "q": {ph: OPP_BASE_OUT[ph] * sr[3] / opp["bat_strength"] for ph in ("PP", "MID", "DEATH")},
            })
        opp_bowlers = []
        for o in team_players:
            if o["bowl_econ"] is None:
                continue
            factor = o["bowl_econ"] / 9.3
            opp_bowlers.append({"id": o["opp_player_id"], "econ": {
                "PP": LEAGUE_ECON["PP"] / opp["bowl_pp"] * factor,
                "MID": LEAGUE_ECON["MID"] / opp["bowl_mid"] * factor,
                "DEATH": LEAGUE_ECON["DEATH"] / opp["bowl_death"] * factor}})

        toss_winner = "RCB" if rng.random() < 0.5 else opp_code
        toss_decision = "BOWL" if rng.random() < 0.68 else "BAT"
        if ipl_no == VALIDATION_IPL_MATCH:
            # Validation scenario is fixed as a bat-first case so all three checkpoints are observable
            toss_winner, toss_decision = "RCB", "BAT"
        rcb_bat_first = (toss_winner == "RCB") == (toss_decision == "BAT")

        order = [("RCB", rcb_lineup, opp_bowlers, opp_code), ("OPP", opp_lineup, rcb_bowlers, "RCB")]
        if not rcb_bat_first:
            order.reverse()

        target = None
        summaries = {}
        for inn_no, (side, lineup, bowlers, bowling_team) in enumerate(order, start=1):
            dels, summ = simulate_innings(rng, match_id=match_id, innings_no=inn_no, batting_side=side,
                                          lineup=lineup, bowlers=bowlers, target=target)
            deliveries.extend(dels)
            summaries[side] = summ
            innings_rows.append({
                "innings_id": summ["innings_id"], "match_id": match_id, "innings_no": inn_no,
                "batting_side": side, "batting_team": "RCB" if side == "RCB" else opp_code,
                "bowling_team": bowling_team, "target": target, "end_reason": summ["end_reason"],
            })
            target = summ["total_runs"] + 1

        r, o = summaries["RCB"], summaries["OPP"]
        if r["total_runs"] > o["total_runs"]:
            winner = "RCB"
            margin = (_plural(r["total_runs"] - o["total_runs"], "run") if rcb_bat_first
                      else _plural(10 - r["wickets"], "wicket"))
        elif o["total_runs"] > r["total_runs"]:
            winner = opp_code
            margin = (_plural(o["total_runs"] - r["total_runs"], "run") if not rcb_bat_first
                      else _plural(10 - o["wickets"], "wicket"))
        else:
            winner = "RCB" if rng.random() < 0.5 else opp_code   # super over (not simulated)
            margin = "Super Over"

        matches.append({
            "match_id": match_id, "ipl_match_no": ipl_no, "rcb_match_no": match_id,
            "match_date": SEASON_START + timedelta(days=offset), "venue_id": venue["venue_id"],
            "opponent_id": opp["team_id"], "is_home": home, "toss_winner": toss_winner,
            "toss_decision": toss_decision, "rcb_batting_first": rcb_bat_first, "status": "COMPLETED",
            "rcb_runs": r["total_runs"], "rcb_wickets": r["wickets"], "rcb_balls": r["legal_balls"],
            "opp_runs": o["total_runs"], "opp_wickets": o["wickets"], "opp_balls": o["legal_balls"],
            "winner": winner, "result_margin": margin, "is_validation_case": ipl_no == VALIDATION_IPL_MATCH,
        })

    return {"matches": matches, "innings": innings_rows, "deliveries": deliveries, "selections": selections}
