"""Formula 15: Bowling Strength Index (BSI).

BSI = clip(LeagueEcon / RCBEcon, 0.85, 1.15)

RCBEcon is the shrunk economy of the bowlers in the selected XI. BSI > 1
means RCB's attack concedes less than the league, so a smaller total is
defensible.
"""


def bowling_strength_index(league_econ: float, rcb_econ: float, lo: float = 0.85, hi: float = 1.15) -> float:
    if rcb_econ <= 0:
        return 1.0
    return float(min(max(league_econ / rcb_econ, lo), hi))
