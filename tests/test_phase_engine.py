import pandas as pd

from backend.engine.phase_engine import innings_checkpoints, phase_breakdown, tag_phases


def _innings(overs: int, runs_per_ball: int = 1, wicket_at: int | None = None):
    rows, n = [], 0
    for o in range(1, overs + 1):
        for b in range(1, 7):
            n += 1
            rows.append({"delivery_id": n, "over_no": o, "runs_batter": runs_per_ball, "runs_extras": 0,
                         "is_legal": True, "is_wicket": n == wicket_at})
    return tag_phases(pd.DataFrame(rows))


def test_tagging_and_breakdown():
    d = _innings(20)
    assert (d.groupby("phase").size().to_dict()) == {"DEATH": 24, "MID": 60, "PP": 36}
    ph = phase_breakdown(d)
    assert ph["PP"]["runs"] == 36 and ph["MID"]["run_rate"] == 6.0


def test_checkpoints_full_innings():
    cp = innings_checkpoints(_innings(20, wicket_at=10), "OVERS")
    assert cp[6] == {"runs": 36, "wickets": 1, "reached": True, "evaluable": True}
    assert cp[20]["runs"] == 120


def test_checkpoints_chase_finished_early():
    cp = innings_checkpoints(_innings(15), "CHASED")
    assert cp[6]["evaluable"] and not cp[16]["evaluable"] and not cp[20]["evaluable"]
