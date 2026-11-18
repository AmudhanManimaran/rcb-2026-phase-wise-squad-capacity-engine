"""Formula 13: Opponent phase threat (economy ratio).

OppThreat(p) = OppEcon(p) / LeagueEcon(p)

Values below 1 mean the opponent concedes less than the league in that
phase (a stronger bowling threat); values above 1 mean it is easier to
score against them.
"""


def opponent_threat(opp_econ: float, league_econ: float) -> float:
    return float(opp_econ / league_econ) if league_econ > 0 else 1.0
