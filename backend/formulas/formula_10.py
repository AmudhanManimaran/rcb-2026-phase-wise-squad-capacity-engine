"""Formula 10: Raw phase scoring capacity and expected wickets.

Cap(p)  = Balls(p) * (TeamSR(p) / 100 + ExtrasRate)
E[W](p) = Balls(p) * TeamOut(p)
"""


def phase_capacity(team_sr: float, team_out: float, balls: int, extras_rate: float = 0.06):
    runs = balls * (team_sr / 100.0 + extras_rate)
    wickets = balls * team_out
    return float(runs), float(wickets)
