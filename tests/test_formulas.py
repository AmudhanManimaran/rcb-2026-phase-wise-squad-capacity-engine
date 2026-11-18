import math

import pytest

from backend import formulas as F


def test_f01_phase_mapping():
    assert [F.phase_of_over(o) for o in (1, 6, 7, 16, 17, 20)] == ["PP", "PP", "MID", "MID", "DEATH", "DEATH"]
    assert F.phase_of_ball(36) == "PP" and F.phase_of_ball(37) == "MID" and F.phase_of_ball(97) == "DEATH"
    assert sum(F.PHASE_BALLS.values()) == 120
    with pytest.raises(ValueError):
        F.phase_of_over(21)


def test_f02_recency_half_life():
    assert F.recency_weight(0) == 1.0
    assert math.isclose(F.recency_weight(70), 0.5)
    assert math.isclose(F.recency_weight(140), 0.25)
    assert F.recency_weight(-5) == 1.0


def test_f03_f04_weighted_rates():
    assert math.isclose(F.weighted_strike_rate([4, 0], [1, 1]), 200.0)
    assert math.isclose(F.weighted_strike_rate([6, 0], [1, 0.5]), 400.0)
    assert math.isclose(F.weighted_out_probability([1, 0, 0, 0], [1, 1, 1, 1]), 0.25)
    assert F.weighted_strike_rate([], []) is None


def test_f05_shrinkage():
    assert F.shrink_to_prior(0, 0, 1.4, 30) == 1.4                     # cold start equals prior
    assert math.isclose(F.shrink_to_prior(200, 100, 1.0, 0), 2.0)       # no prior weight
    est = F.shrink_to_prior(200, 100, 1.0, 100)
    assert math.isclose(est, 1.5)


def test_f06_expected_balls():
    assert F.expected_phase_balls([], [], 15.0, 2.0) == 15.0
    assert math.isclose(F.expected_phase_balls([20, 20], [1, 1], 10.0, 2.0), 15.0)
    for phase, total in (("PP", 36), ("MID", 60), ("DEATH", 24)):
        assert math.isclose(sum(F.SLOT_BALL_TEMPLATE[s][phase] for s in range(1, 12)), total, abs_tol=0.01)


def test_f07_to_f10_team_capacity():
    shares = F.ball_share({1: 30, 2: 10})
    assert math.isclose(sum(shares.values()), 1.0) and math.isclose(shares[1], 0.75)
    assert math.isclose(F.team_strike_rate(shares, {1: 160, 2: 120}), 150.0)
    assert math.isclose(F.team_out_probability(shares, {1: 0.04, 2: 0.08}), 0.05)
    runs, wkts = F.phase_capacity(150, 0.05, 36, 0.05)
    assert math.isclose(runs, 36 * 1.55) and math.isclose(wkts, 1.8)


def test_f11_f12_venue():
    s = F.venue_phase_share({"PP": 60, "MID": 90, "DEATH": 50})
    assert math.isclose(sum(s.values()), 1.0) and math.isclose(s["MID"], 0.45)
    assert F.blended_average(None, 0, 55.0) == 55.0
    assert math.isclose(F.blended_average(70.0, 3, 50.0, 3), 60.0)
    assert math.isclose(F.venue_phase_factor(60, 50), 1.2)


def test_f13_f14_opponent_adjustment():
    assert math.isclose(F.opponent_threat(8.0, 10.0), 0.8)
    r, w = F.adjusted_capacity(100, 4, 1.1, 0.8, alpha=1, beta=1)
    assert math.isclose(r, 88.0) and math.isclose(w, 5.0)
    r0, w0 = F.adjusted_capacity(100, 4, 1.1, 0.8, alpha=0, beta=0)
    assert r0 == 100 and w0 == 4


def test_f15_f16_targets():
    assert F.bowling_strength_index(9.0, 9.0) == 1.0
    assert F.bowling_strength_index(9.0, 6.0) == 1.15                  # clipped
    assert F.base_target(180, 200, 0.5) == 190
    assert math.isclose(F.recommended_target(200, 1.1), 180.0)


def test_f17_f18_f19():
    t = F.venue_shaped_targets(200, {"PP": 0.3, "MID": 0.45, "DEATH": 0.25})
    assert math.isclose(sum(t.values()), 200)
    assert F.checkpoint_cost(60, 55, 2, 4) == 13
    assert F.wicket_resource(2) == 1.0 and F.wicket_resource(13) == 0.35
    extra = F.deficit_carry_forward(20, {"MID": 3, "DEATH": 1})
    assert math.isclose(extra["MID"], 15) and math.isclose(sum(extra.values()), 20)


def test_f20_metrics():
    assert F.mae([10, 20], [12, 16]) == 3.0
    assert math.isclose(F.bias([10, 20], [12, 16]), 1.0)
    assert math.isclose(F.rel_error(110, 100), 0.1)
    assert F.within_tolerance(190, 200, 20) and not F.within_tolerance(170, 200, 20)
    assert len(F.FORMULA_CATALOGUE) == 20
