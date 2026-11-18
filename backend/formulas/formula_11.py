"""Formula 11: Venue phase share.

s_p = V_bar_p / V_bar,  V_bar = sum_p V_bar_p

The share of a venue's typical innings scored in each phase.
"""


def venue_phase_share(venue_phase_avgs: dict) -> dict:
    total = sum(venue_phase_avgs.values())
    return {p: (v / total if total > 0 else 1.0 / len(venue_phase_avgs)) for p, v in venue_phase_avgs.items()}
