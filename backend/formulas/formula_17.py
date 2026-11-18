"""Formula 17: Venue-shaped phase targets.

R_p_target = T * s_p
"""


def venue_shaped_targets(total_target: float, shares: dict) -> dict:
    return {p: float(total_target * s) for p, s in shares.items()}
