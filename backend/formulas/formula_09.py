"""Formula 09: Team phase dismissal probability per ball.

TeamOut(p) = sum_i BallShare_i(p) * OutProb(i,p)
"""


def team_out_probability(shares: dict, out_probs: dict) -> float:
    return float(sum(shares[i] * out_probs[i] for i in shares))
