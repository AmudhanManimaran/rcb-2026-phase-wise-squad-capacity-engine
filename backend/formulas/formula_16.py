"""Formula 16: Base and recommended first-innings target.

T_base        = lambda * VenuePar + (1 - lambda) * Capacity
T_recommended = T_base * (2 - BSI)

lambda (target weight) is fitted during calibration.
"""


def base_target(venue_par: float, capacity: float, lam: float = 0.5) -> float:
    return float(lam * venue_par + (1.0 - lam) * capacity)


def recommended_target(t_base: float, bsi: float) -> float:
    return float(t_base * (2.0 - bsi))
