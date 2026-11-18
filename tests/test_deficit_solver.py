import pytest

from backend.engine.deficit_solver import evaluate_state, expected_at, overs_text, parse_overs

PLAN = [{"phase": "PP", "planned_phase_runs": 54.0, "planned_phase_wkts": 1.2},
        {"phase": "MID", "planned_phase_runs": 90.0, "planned_phase_wkts": 2.8},
        {"phase": "DEATH", "planned_phase_runs": 48.0, "planned_phase_wkts": 2.0}]
CAP = {"PP": {"adj_runs": 54.0, "adj_wickets": 1.2}, "MID": {"adj_runs": 90.0, "adj_wickets": 2.8},
       "DEATH": {"adj_runs": 48.0, "adj_wickets": 2.0}}


def test_parse_overs():
    assert parse_overs("12.3") == 75 and parse_overs("20") == 120 and overs_text(75) == "12.3"
    with pytest.raises(ValueError):
        parse_overs("12.7")


def test_expected_runs_linear_within_phase():
    assert expected_at(PLAN, 36) == 54.0
    assert expected_at(PLAN, 66) == 54.0 + 45.0
    assert expected_at(PLAN, 120) == 192.0


def test_deficit_redistributed_over_remaining_phases():
    s = evaluate_state(PLAN, CAP, legal_balls=66, runs=79, wickets=3, plan_target=192.0)
    assert s["deficit"] == pytest.approx(20.0)
    assert sum(r["extra_runs"] for r in s["recommendations"]) == pytest.approx(20.0, abs=0.05)
    assert {r["phase"] for r in s["recommendations"]} == {"MID", "DEATH"}
    assert s["status"] in ("BEHIND", "CRITICAL")
    assert sum(r["is_primary"] for r in s["recommendations"]) == 1


def test_ahead_of_plan():
    s = evaluate_state(PLAN, CAP, legal_balls=36, runs=70, wickets=0, plan_target=192.0)
    assert s["status"] == "AHEAD" and s["deficit"] < 0
