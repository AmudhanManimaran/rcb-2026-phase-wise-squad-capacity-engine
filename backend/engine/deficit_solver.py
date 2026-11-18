"""Live deficit tracking and carry-forward allocation (formula 19)."""
from backend.formulas import PHASE_BALLS, PHASES, deficit_carry_forward, phase_of_ball, wicket_resource

PHASE_START = {"PP": 0, "MID": 36, "DEATH": 96}


def parse_overs(overs: str | float) -> int:
    """'12.3' -> 75 legal balls."""
    s = str(overs).strip()
    if "." in s:
        o, b = s.split(".", 1)
        o, b = int(o or 0), int(b or 0)
    else:
        o, b = int(float(s)), 0
    if not (0 <= b <= 5) or o < 0 or o * 6 + b > 120:
        raise ValueError("overs must look like 12.3 with balls 0-5 and at most 20 overs")
    return o * 6 + b


def overs_text(balls: int) -> str:
    return f"{balls // 6}.{balls % 6}"


def expected_at(plan: list[dict], legal_balls: int, key: str = "planned_phase_runs") -> float:
    """Plan cumulative runs at a legal-ball count, linear within each phase."""
    total = 0.0
    for c in plan:
        p = c["phase"]
        start, n = PHASE_START[p], PHASE_BALLS[p]
        done = min(max(legal_balls - start, 0), n)
        total += c[key] * done / n
    return total


def expected_wkts_at(plan: list[dict], legal_balls: int) -> float:
    return expected_at(plan, legal_balls, "planned_phase_wkts")


def evaluate_state(plan: list[dict], capacity: dict, legal_balls: int, runs: int, wickets: int,
                   plan_target: float) -> dict:
    """Deficit vs plan and redistribution across the remaining phases.

    capacity: {phase: {'adj_runs': x, 'adj_wickets': y}}
    """
    exp_runs = expected_at(plan, legal_balls)
    exp_wkts = expected_wkts_at(plan, legal_balls)
    deficit = exp_runs - runs                       # positive = behind
    resource = wicket_resource(wickets) / wicket_resource(exp_wkts)
    current_phase = phase_of_ball(legal_balls + 1) if legal_balls < 120 else "DEATH"

    eff, rows = {}, []
    for c in plan:
        p = c["phase"]
        start, n = PHASE_START[p], PHASE_BALLS[p]
        rem = n - min(max(legal_balls - start, 0), n)
        if rem <= 0:
            continue
        cap_rpb = capacity[p]["adj_runs"] / n
        eff[p] = cap_rpb * rem * resource
        rows.append({"phase": p, "balls_remaining": rem, "planned_runs": round(c["planned_phase_runs"] * rem / n, 2),
                     "capacity_rr": round(6 * cap_rpb * resource, 2)})

    extras = deficit_carry_forward(deficit, eff)
    for r in rows:
        r["efficiency"] = round(eff[r["phase"]], 4)
        r["extra_runs"] = round(extras[r["phase"]], 2)
        r["revised_runs"] = round(max(0.0, r["planned_runs"] + r["extra_runs"]), 2)
        r["required_rr"] = round(6 * r["revised_runs"] / r["balls_remaining"], 2)
        ratio = r["required_rr"] / r["capacity_rr"] if r["capacity_rr"] > 0 else 9.9
        r["risk_level"] = "LOW" if ratio <= 1.05 else ("MEDIUM" if ratio <= 1.25 else "HIGH")
        r["is_primary"] = False
    if rows:
        primary = max(rows, key=lambda r: r["extra_runs"]) if deficit > 0 else max(rows, key=lambda r: r["efficiency"])
        primary["is_primary"] = True

    projected_total = runs + sum(eff.values())
    if deficit <= -5:
        status = "AHEAD"
    elif deficit < 5:
        status = "ON_TRACK"
    elif deficit <= 15 and not any(r["risk_level"] == "HIGH" for r in rows):
        status = "BEHIND"
    else:
        status = "CRITICAL"

    balls_left = 120 - legal_balls
    need = plan_target - runs
    message = _message(status, deficit, rows, need, balls_left, wickets)
    return {"legal_balls": legal_balls, "overs": overs_text(legal_balls), "runs": runs, "wickets": wickets,
            "current_phase": current_phase, "expected_runs": round(exp_runs, 2), "expected_wkts": round(exp_wkts, 2),
            "deficit": round(deficit, 2), "projected_total": round(projected_total, 2), "status": status,
            "plan_target": round(plan_target, 2), "runs_needed": round(need, 2),
            "overall_required_rr": round(6 * need / balls_left, 2) if balls_left else None,
            "recommendations": rows, "message": message}


def _message(status, deficit, rows, need, balls_left, wickets):
    if not rows:
        return "Innings complete."
    prim = next(r for r in rows if r["is_primary"])
    if status == "AHEAD":
        return (f"Ahead of plan by {abs(deficit):.0f} runs. Protect wickets ({10 - wickets} in hand) and hold "
                f"{prim['phase']} at {prim['required_rr']:.1f} per over.")
    if status == "ON_TRACK":
        return f"On plan. Need {need:.0f} from {balls_left} balls; keep {prim['phase']} at {prim['required_rr']:.1f} per over."
    return (f"Behind plan by {deficit:.0f} runs. Largest recovery share goes to {prim['phase']}: "
            f"+{prim['extra_runs']:.0f} runs, required {prim['required_rr']:.1f} per over "
            f"(capacity {prim['capacity_rr']:.1f}, risk {prim['risk_level']}).")
