"""Formula 12: Venue phase scoring factor.

VF(p) = V_bar_p(venue) / L_bar_p(league)

Blended venue average uses Bayesian shrinkage toward the venue prior:
V_bar_p = (n * observed + k_v * prior) / (n + k_v)
"""


def blended_average(observed_mean, n: int, prior: float, k: float = 3.0) -> float:
    if observed_mean is None or n <= 0:
        return float(prior)
    return float((n * observed_mean + k * prior) / (n + k))


def venue_phase_factor(venue_avg: float, league_avg: float) -> float:
    return float(venue_avg / league_avg) if league_avg > 0 else 1.0
