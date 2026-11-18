"""Formula 19: Deficit carry-forward.

Extra_q = Deficit * Eff(q) / sum_{r in remaining} Eff(r)

Eff(q) = capacity run rate of phase q * balls remaining in q * wicket resource.
A positive deficit (behind plan) is redistributed across the remaining
phases in proportion to their scoring efficiency.
"""


def deficit_carry_forward(deficit: float, efficiencies: dict) -> dict:
    total = sum(max(e, 0.0) for e in efficiencies.values())
    if total <= 0:
        return {q: 0.0 for q in efficiencies}
    return {q: float(deficit * max(e, 0.0) / total) for q, e in efficiencies.items()}
