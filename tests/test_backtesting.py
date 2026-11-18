from backend.backtesting.chronological_runner import run_chronological
from backend.backtesting.metrics import objective, summarise
from backend.engine.pipeline import predict_match
from backend.engine.season_data import EngineParams
from tests.conftest import requires_db


@requires_db
def test_no_future_leakage(season):
    for _, m in season.matches.iterrows():
        mid = int(m["match_id"])
        hist = season.history_match_ids(mid)
        assert all(season.match(h)["match_date"] < m["match_date"] for h in hist)
        assert mid not in hist


@requires_db
def test_first_match_is_pure_cold_start(season):
    first = int(season.matches.sort_values("match_date").iloc[0]["match_id"])
    pred = predict_match(season, first, EngineParams())
    assert pred["history_matches"] == 0
    assert all(p["cold_start"] for p in pred["player_profiles"])
    assert all(p["sr"] == p["prior_sr"] for p in pred["player_profiles"])


@requires_db
def test_prediction_independent_of_future_results(season):
    """Changing a later match's deliveries must not change an earlier prediction."""
    mid = 5
    before = predict_match(season, mid, EngineParams())["capacity_total"]
    from copy import deepcopy
    altered = deepcopy(season)
    altered._cache.clear()
    later = altered.deliveries["match_id"] > mid
    altered.deliveries.loc[later, "runs_batter"] = 6
    after = predict_match(altered, mid, EngineParams())["capacity_total"]
    assert before == after


@requires_db
def test_chronological_backtest_metrics(season):
    run = run_chronological(season, EngineParams())
    s = summarise(run["results"])
    assert s["matches_evaluated"] == len(season.matches)
    assert s["n_6"] == len(season.matches)
    assert 0 < s["mae_20"] < 60 and 0 <= s["hit_rate"] <= 1
    assert objective(run["results"]) > 0
