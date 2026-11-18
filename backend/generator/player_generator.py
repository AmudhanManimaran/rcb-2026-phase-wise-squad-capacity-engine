"""Synthetic player ability generator.

Each RCB player gets a season talent multiplier around his prior plus a
match-to-match form process (AR(1)), so recent matches carry more signal
than old ones, which is what the 70-day recency decay is designed to
capture. Opponent squads are generated as role-based placeholders.
"""
import numpy as np

LEAGUE_ECON = {"PP": 9.10, "MID": 8.48, "DEATH": 12.40}   # mean of venue priors (runs per over)

OPP_SLOT_PROFILE = {   # slot: (SR PP, SR MID, SR DEATH, out-prob multiplier, role)
    1: (150, 138, 165, 1.00, "BAT"), 2: (144, 136, 165, 1.00, "BAT"), 3: (138, 142, 170, 1.00, "BAT"),
    4: (132, 146, 180, 1.05, "BAT"), 5: (128, 148, 190, 1.10, "WK"), 6: (124, 146, 196, 1.15, "AR"),
    7: (118, 136, 186, 1.25, "AR"), 8: (100, 112, 140, 1.70, "BOWL"), 9: (90, 100, 125, 2.00, "BOWL"),
    10: (80, 90, 110, 2.30, "BOWL"), 11: (70, 80, 100, 2.60, "BOWL"),
}
OPP_BASE_OUT = {"PP": 0.040, "MID": 0.042, "DEATH": 0.065}


def rcb_season_abilities(players: list[dict], n_matches: int, rng: np.random.Generator) -> dict:
    """Return {player_id: {'talent_sr', 'talent_out', 'form': [n_matches]}}."""
    out = {}
    for p in players:
        form = np.zeros(n_matches)
        f = rng.normal(0, 0.04)
        for m in range(n_matches):
            f = 0.70 * f + rng.normal(0, 0.055)
            form[m] = f
        out[p["player_id"]] = {
            "talent_sr": float(np.exp(rng.normal(0, 0.06))),
            "talent_out": float(np.exp(rng.normal(0, 0.12))),
            "form": form,
        }
    return out


def generate_opponent_players(teams: list[dict], rng: np.random.Generator) -> list[dict]:
    rows = []
    for t in teams:
        for slot in range(1, 12):
            sr_pp, sr_mid, sr_death, out_mult, role = OPP_SLOT_PROFILE[slot]
            label = {"BAT": "Batter", "WK": "Keeper", "AR": "All-rounder", "BOWL": "Bowler"}[role]
            bowls = slot >= 6
            rows.append({
                "opp_player_id": t["team_id"] * 100 + slot,
                "team_id": t["team_id"],
                "player_name": f"{t['team_code']} {label} {slot}",
                "role": role,
                "slot": slot,
                "bat_sr_factor": round(float(np.exp(rng.normal(0, 0.05))), 3),
                "bowl_econ": round(float(np.exp(rng.normal(0, 0.05))) * 9.3, 2) if bowls else None,
            })
    return rows
