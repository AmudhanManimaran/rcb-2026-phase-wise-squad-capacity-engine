"""Actual RCB checkpoints for a completed match (ground truth for backtesting)."""
from backend.engine.phase_engine import innings_checkpoints, phase_breakdown
from backend.engine.season_data import SeasonData


def actual_rcb_checkpoints(data: SeasonData, match_id: int) -> dict | None:
    inn = data.innings[(data.innings["match_id"] == match_id) & (data.innings["batting_side"] == "RCB")]
    if inn.empty:
        return None
    inn = inn.iloc[0]
    d = data.deliveries[data.deliveries["innings_id"] == inn["innings_id"]]
    if d.empty:
        return None
    return {"innings_id": int(inn["innings_id"]), "end_reason": inn["end_reason"],
            "total_runs": int(inn["total_runs"]), "wickets": int(inn["wickets"]),
            "legal_balls": int(inn["legal_balls"]),
            "checkpoints": innings_checkpoints(d, inn["end_reason"]), "phases": phase_breakdown(d)}
