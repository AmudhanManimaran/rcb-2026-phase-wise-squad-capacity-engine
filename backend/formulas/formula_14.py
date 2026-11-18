"""Formula 14: Venue- and opponent-adjusted phase capacity.

AdjCap(p)  = Cap(p) * VF(p)^beta * OppThreat(p)^alpha
AdjW(p)    = E[W](p) * OppThreat(p)^(-alpha)

alpha and beta are calibration exponents (1.0 = full adjustment).
"""


def adjusted_capacity(cap_runs: float, exp_wkts: float, venue_factor: float, threat: float,
                      alpha: float = 1.0, beta: float = 1.0):
    runs = cap_runs * (venue_factor ** beta) * (threat ** alpha)
    wkts = exp_wkts * (threat ** (-alpha))
    return float(runs), float(wkts)
