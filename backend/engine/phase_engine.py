"""Phase tagging and checkpoint extraction (formula 01)."""
import pandas as pd

from backend.formulas import CHECKPOINT_OVER, PHASES, phase_of_over


def tag_phases(deliveries: pd.DataFrame) -> pd.DataFrame:
    out = deliveries.copy()
    out["phase"] = out["over_no"].astype(int).map(phase_of_over)
    return out


def innings_checkpoints(innings_deliveries: pd.DataFrame, end_reason: str | None = None) -> dict:
    """Runs and wickets at the end of overs 6, 16 and 20 for one innings.

    A checkpoint is `evaluable` when the innings reached that over, or the
    side was bowled out before it (a genuine shortfall). It is not
    evaluable when a chase finished before that over.
    """
    d = innings_deliveries.sort_values("delivery_id")
    total_legal = int(d["is_legal"].sum())
    final_wkts = int(d["is_wicket"].sum())
    result = {}
    for phase in PHASES:
        over = CHECKPOINT_OVER[phase]
        upto = d[d["over_no"] <= over]
        runs = int(upto["runs_batter"].sum() + upto["runs_extras"].sum())
        wkts = int(upto["is_wicket"].sum())
        reached = total_legal >= over * 6
        all_out = final_wkts >= 10
        evaluable = reached or (all_out and end_reason != "CHASED")
        result[over] = {"runs": runs, "wickets": wkts, "reached": reached, "evaluable": bool(evaluable)}
    return result


def phase_breakdown(innings_deliveries: pd.DataFrame) -> dict:
    d = innings_deliveries
    out = {}
    for phase in PHASES:
        p = d[d["phase"] == phase]
        balls = int(p["is_legal"].sum())
        runs = int(p["runs_batter"].sum() + p["runs_extras"].sum())
        out[phase] = {"runs": runs, "wickets": int(p["is_wicket"].sum()), "balls": balls,
                      "run_rate": round(6 * runs / balls, 2) if balls else None}
    return out
