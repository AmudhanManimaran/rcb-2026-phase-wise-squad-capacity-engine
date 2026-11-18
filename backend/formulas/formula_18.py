"""Formula 18: Checkpoint solver cost.

Cost = |Runs - R_target| + w * E[Wickets]

Used as the stage cost of the dynamic-programming checkpoint solver,
evaluated on cumulative runs at each checkpoint so that early shortfalls
must be recovered later.
"""


def checkpoint_cost(runs: float, target: float, exp_wickets: float, wicket_penalty: float) -> float:
    return float(abs(runs - target) + wicket_penalty * exp_wickets)


def wicket_resource(wickets_lost: float) -> float:
    """Scoring resource left with a given number of wickets down (1.0 = full)."""
    return float(max(0.35, 1.0 - 0.07 * max(0.0, wickets_lost - 3.0)))
