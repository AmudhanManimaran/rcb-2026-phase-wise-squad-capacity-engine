"""Predicted vs actual comparison per checkpoint (formula 20)."""
from backend.formulas import abs_error, rel_error, within_tolerance


def evaluate_checkpoints(projection: list[dict], actual: dict) -> list[dict]:
    rows = []
    for p in projection:
        over = p["checkpoint_over"]
        a = actual["checkpoints"][over]
        row = {"checkpoint_over": over, "phase": p["phase"], "predicted_runs": p["projected_runs"],
               "predicted_wkts": p["projected_wkts"], "actual_runs": a["runs"], "actual_wkts": a["wickets"],
               "evaluable": a["evaluable"]}
        if a["evaluable"]:
            row["abs_error"] = round(abs_error(p["projected_runs"], a["runs"]), 2)
            re_ = rel_error(p["projected_runs"], a["runs"])
            row["rel_error"] = None if re_ is None else round(re_, 4)
            row["within_tolerance"] = within_tolerance(p["projected_runs"], a["runs"], over)
        else:
            row.update(abs_error=None, rel_error=None, within_tolerance=None)
        rows.append(row)
    return rows
