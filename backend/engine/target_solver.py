"""Target recommendation and dynamic-programming checkpoint solver.

Formulas 15-18. The solver chooses an intent level per phase (scoring
aggression relative to the XI's adjusted capacity). Higher intent raises
phase runs but also expected wickets, and wickets lost above the baseline
erode the scoring resource of later phases. The DP minimises the summed
checkpoint cost |CumRuns - CumTarget| + w * E[Wickets].
"""
from functools import lru_cache

import numpy as np

from backend.formulas import (CHECKPOINT_OVER, PHASES, base_target, checkpoint_cost, recommended_target,
                              venue_shaped_targets, wicket_resource)

INTENTS = tuple(float(round(x, 2)) for x in np.arange(0.80, 1.251, 0.05))
WICKET_ELASTICITY = 2.2      # wickets scale with intent^2.2
FINAL_WEIGHT = 1.5           # extra emphasis on the 20-over checkpoint


def recommend_target(venue_par: float, capacity_total: float, bsi: float, lam: float) -> dict:
    t_base = base_target(venue_par, capacity_total, lam)
    return {"t_base": round(t_base, 2), "bsi": round(bsi, 3), "t_recommended": round(recommended_target(t_base, bsi), 2)}


def solve_checkpoints(adj_runs: dict, adj_wkts: dict, plan_target: float, shares: dict, wicket_penalty: float) -> dict:
    """Dynamic programme over (phase, cumulative runs, cumulative wickets)."""
    targets = venue_shaped_targets(plan_target, shares)
    cum_targets, acc = {}, 0.0
    for p in PHASES:
        acc += targets[p]
        cum_targets[p] = acc
    base_w_before, acc = {}, 0.0
    for p in PHASES:
        base_w_before[p] = acc
        acc += adj_wkts[p]

    @lru_cache(maxsize=None)
    def best(stage: int, runs_q: int, wkts_q: int):
        if stage == len(PHASES):
            return 0.0, ()
        p = PHASES[stage]
        runs, wkts = runs_q / 4.0, wkts_q / 20.0
        resource = wicket_resource(wkts) / wicket_resource(base_w_before[p])
        best_val, best_path = float("inf"), ()
        for a in INTENTS:
            pr = adj_runs[p] * a * resource
            pw = adj_wkts[p] * a ** WICKET_ELASTICITY
            new_runs, new_wkts = runs + pr, min(10.0, wkts + pw)
            cost = checkpoint_cost(new_runs, cum_targets[p], pw, wicket_penalty)
            if stage == len(PHASES) - 1:
                cost *= FINAL_WEIGHT
            nxt, path = best(stage + 1, int(round(new_runs * 4)), int(round(new_wkts * 20)))
            if cost + nxt < best_val:
                best_val, best_path = cost + nxt, ((a, pr, pw),) + path
        return best_val, best_path

    total_cost, path = best(0, 0, 0)
    plan, cum_r, cum_w = [], 0.0, 0.0
    for p, (a, pr, pw) in zip(PHASES, path):
        cum_r += pr
        cum_w = min(10.0, cum_w + pw)
        plan.append({"phase": p, "checkpoint_over": CHECKPOINT_OVER[p], "intent": a,
                     "target_phase_runs": round(targets[p], 2), "target_cum_runs": round(cum_targets[p], 2),
                     "planned_phase_runs": round(pr, 2), "planned_phase_wkts": round(pw, 2),
                     "planned_cum_runs": round(cum_r, 2), "planned_cum_wkts": round(cum_w, 2)})
    return {"plan_target": round(plan_target, 2), "total_cost": round(total_cost, 3), "checkpoints": plan}


def projection(adj_runs: dict, adj_wkts: dict) -> list[dict]:
    """Capacity projection (intent 1.0) used for backtesting."""
    out, r, w = [], 0.0, 0.0
    for p in PHASES:
        r += adj_runs[p]
        w = min(10.0, w + adj_wkts[p])
        out.append({"phase": p, "checkpoint_over": CHECKPOINT_OVER[p], "projected_runs": round(r, 2),
                    "projected_wkts": round(w, 2), "phase_runs": round(adj_runs[p], 2)})
    return out
