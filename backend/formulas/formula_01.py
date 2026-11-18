"""Formula 01: Phase assignment.

phase(over) = PP for overs 1-6, MID for overs 7-16, DEATH for overs 17-20.
Each phase has a fixed legal-ball budget: PP 36, MID 60, DEATH 24.
"""

PHASES = ("PP", "MID", "DEATH")
PHASE_BALLS = {"PP": 36, "MID": 60, "DEATH": 24}
PHASE_OVERS = {"PP": (1, 6), "MID": (7, 16), "DEATH": (17, 20)}
CHECKPOINT_OVER = {"PP": 6, "MID": 16, "DEATH": 20}


def phase_of_over(over_no: int) -> str:
    """Return the phase code for a 1-based over number."""
    if 1 <= over_no <= 6:
        return "PP"
    if 7 <= over_no <= 16:
        return "MID"
    if 17 <= over_no <= 20:
        return "DEATH"
    raise ValueError(f"over_no must be 1..20, got {over_no}")


def phase_of_ball(legal_ball_no: int) -> str:
    """Phase of the n-th legal ball (1..120)."""
    return phase_of_over((legal_ball_no - 1) // 6 + 1)
