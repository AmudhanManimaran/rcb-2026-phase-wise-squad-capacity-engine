"""Formula 08: Team phase strike rate.

TeamSR(p) = sum_i BallShare_i(p) * SR(i,p)
"""


def team_strike_rate(shares: dict, strike_rates: dict) -> float:
    return float(sum(shares[i] * strike_rates[i] for i in shares))
