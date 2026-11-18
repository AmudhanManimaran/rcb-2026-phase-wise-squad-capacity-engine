import pandas as pd

from backend.engine.team_capacity_engine import compute_team_capacity, extras_rate


def test_team_capacity_from_profiles():
    rows = []
    for pid, (sr, out, balls) in {1: (150, 0.04, 20), 2: (130, 0.03, 16)}.items():
        for ph in ("PP", "MID", "DEATH"):
            rows.append({"player_id": pid, "phase": ph, "sr": sr, "out_prob": out, "exp_balls": balls})
    profiles, cap = compute_team_capacity(pd.DataFrame(rows), pd.DataFrame(columns=["is_legal", "runs_extras"]))
    for ph in ("PP", "MID", "DEATH"):
        assert abs(profiles[profiles["phase"] == ph]["ball_share"].sum() - 1) < 1e-3
    pp = cap[cap["phase"] == "PP"].iloc[0]
    expected_sr = (20 * 150 + 16 * 130) / 36
    assert abs(pp["team_sr"] - expected_sr) < 0.01
    assert abs(pp["raw_runs"] - 36 * (expected_sr / 100 + pp["extras_rate"])) < 0.05


def test_extras_rate_prior_only():
    assert abs(extras_rate(pd.DataFrame(columns=["is_legal", "runs_extras"])) - 0.055) < 1e-9
