"""Failure-mode classification of a backtested match."""
from backend.formulas import CHECKPOINT_TOLERANCE


def classify_match(projection: list[dict], actual: dict) -> str:
    proj = {p["checkpoint_over"]: p for p in projection}
    cp = actual["checkpoints"]
    ph = actual["phases"]
    pred_pp = proj[6]["projected_runs"]
    pred_mid = proj[16]["projected_runs"] - proj[6]["projected_runs"]
    pred_death = proj[20]["projected_runs"] - proj[16]["projected_runs"]

    if actual["end_reason"] == "CHASED" and not cp[20]["evaluable"]:
        if cp[6]["evaluable"] and cp[6]["runs"] > pred_pp + CHECKPOINT_TOLERANCE[6]:
            return "Chase finished early (fast start)"
        return "Chase finished early"
    if actual["end_reason"] == "ALL_OUT" and actual["legal_balls"] < 120:
        return "Batting collapse"
    if cp[6]["runs"] < pred_pp - 10 or cp[6]["wickets"] >= proj[6]["projected_wkts"] + 2:
        return "Powerplay shortfall"
    if ph["MID"]["runs"] < pred_mid - 15:
        return "Middle-overs stall"
    if ph["DEATH"]["runs"] < pred_death - 12:
        return "Death-overs shortfall"
    if cp[20]["runs"] > proj[20]["projected_runs"] + CHECKPOINT_TOLERANCE[20]:
        return "Over-performance"
    if abs(cp[20]["runs"] - proj[20]["projected_runs"]) <= CHECKPOINT_TOLERANCE[20]:
        return "Accurate"
    return "Moderate deviation"
