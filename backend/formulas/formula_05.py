"""Formula 05: Cold-start shrinkage toward the player prior.

est = (sum_t w_t * x_t + k * prior) / (sum_t w_t + k)

k is a pseudo-sample size (in weighted balls). With no 2026 history the
estimate equals the synthetic prior; as weighted evidence grows the
observed value dominates. Applied to both SR (as runs per ball) and OutProb.
"""


def shrink_to_prior(weighted_sum: float, weight_total: float, prior: float, k: float) -> float:
    if weight_total + k <= 0:
        return float(prior)
    return float((weighted_sum + k * prior) / (weight_total + k))
