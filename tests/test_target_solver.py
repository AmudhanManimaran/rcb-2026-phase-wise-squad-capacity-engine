from backend.engine.target_solver import INTENTS, projection, recommend_target, solve_checkpoints

ADJ_RUNS = {"PP": 56.0, "MID": 88.0, "DEATH": 46.0}
ADJ_WKTS = {"PP": 1.2, "MID": 2.8, "DEATH": 2.0}
SHARES = {"PP": 56 / 190, "MID": 88 / 190, "DEATH": 46 / 190}


def test_target_equal_to_capacity_keeps_baseline_intent():
    plan = solve_checkpoints(ADJ_RUNS, ADJ_WKTS, 190.0, SHARES, wicket_penalty=0.0)
    assert [c["intent"] for c in plan["checkpoints"]] == [1.0, 1.0, 1.0]
    assert abs(plan["checkpoints"][-1]["planned_cum_runs"] - 190.0) < 0.5


def test_higher_target_raises_intent_and_is_monotonic():
    plan = solve_checkpoints(ADJ_RUNS, ADJ_WKTS, 215.0, SHARES, wicket_penalty=2.0)
    intents = [c["intent"] for c in plan["checkpoints"]]
    assert all(i in INTENTS for i in intents) and max(intents) > 1.0
    cum = [c["planned_cum_runs"] for c in plan["checkpoints"]]
    assert cum == sorted(cum)


def test_wicket_penalty_reduces_aggression():
    lo = solve_checkpoints(ADJ_RUNS, ADJ_WKTS, 215.0, SHARES, wicket_penalty=0.0)
    hi = solve_checkpoints(ADJ_RUNS, ADJ_WKTS, 215.0, SHARES, wicket_penalty=15.0)
    assert hi["checkpoints"][-1]["planned_cum_wkts"] <= lo["checkpoints"][-1]["planned_cum_wkts"]


def test_projection_and_target():
    proj = projection(ADJ_RUNS, ADJ_WKTS)
    assert [p["projected_runs"] for p in proj] == [56.0, 144.0, 190.0]
    t = recommend_target(180.0, 190.0, 1.05, 0.5)
    assert t["t_base"] == 185.0 and abs(t["t_recommended"] - 175.75) < 0.01
