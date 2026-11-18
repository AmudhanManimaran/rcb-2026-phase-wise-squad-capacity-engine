import pytest
from fastapi.testclient import TestClient

from tests.conftest import requires_db

pytestmark = requires_db


@pytest.fixture(scope="module")
def client():
    from backend.main import app
    return TestClient(app)


@pytest.mark.parametrize("path", ["/api/health", "/api/dashboard", "/api/squad", "/api/squad/2", "/api/matches",
                                  "/api/matches/1", "/api/matches/14/capacity", "/api/backtest/results",
                                  "/api/backtest/parameters", "/api/analytics/phases", "/api/analytics/venues",
                                  "/api/analytics/players", "/api/capacity/formulas", "/api/tracker/14/replay"])
def test_get_endpoints(client, path):
    r = client.get(path)
    assert r.status_code == 200, r.text


def test_plan_and_tracker_flow(client):
    r = client.post("/api/targets/plan", json={"match_id": 14, "plan_mode": "BAT_FIRST", "wicket_penalty": 4})
    assert r.status_code == 200
    plan = r.json()
    assert len(plan["plan"]["checkpoints"]) == 3 and plan["prediction_id"] > 0
    saved = client.get("/api/targets/14").json()
    assert saved["prediction"]["prediction_id"] == plan["prediction_id"]

    r = client.post("/api/tracker/update", json={"match_id": 14, "overs": "10.0", "runs": 80, "wickets": 2})
    assert r.status_code == 200
    st = r.json()
    assert st["prediction_id"] == plan["prediction_id"] and st["legal_balls"] == 60
    assert client.get("/api/tracker/14/recommendation").status_code == 200
    assert client.delete("/api/tracker/14").json()["deleted"] >= 1


def test_custom_xi_validation(client):
    assert client.post("/api/targets/plan", json={"match_id": 14, "xi_player_ids": [1, 2, 3]}).status_code == 400
    overseas_heavy = [1, 7, 9, 11, 15, 2, 3, 4, 5, 6, 8]
    assert client.post("/api/matches/14/capacity", json={"xi_player_ids": overseas_heavy}).status_code == 400
    ok = [1, 2, 15, 4, 5, 6, 7, 8, 19, 10, 11]
    r = client.post("/api/matches/14/capacity", json={"xi_player_ids": ok})
    assert r.status_code == 200 and r.json()["custom_xi"] is True


def test_errors(client):
    assert client.get("/api/matches/99").status_code == 404
    assert client.post("/api/tracker/update", json={"match_id": 14, "overs": "9.7", "runs": 1, "wickets": 0}).status_code == 422
