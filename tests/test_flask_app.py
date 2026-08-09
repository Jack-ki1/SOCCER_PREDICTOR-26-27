"""Integration tests for the Flask app — every page and API route should
respond without error, using an isolated in-memory SQLite DB (not the
project's real epl_predictor.db)."""
import pytest


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("EPL_DB_URL", f"sqlite:///{tmp_path}/test.db")
    monkeypatch.setenv("EPL_ENABLE_SCHEDULER", "false")

    # Reload settings/connection so the env var above actually takes effect —
    # both modules cache module-level state that was likely already
    # imported by the time this fixture runs.
    import importlib

    import config.settings
    import database.connection

    importlib.reload(config.settings)
    importlib.reload(database.connection)

    from database.migrations import run_migrations, seed
    run_migrations()
    seed()

    from dashboard.app import create_app
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client()


PAGE_ROUTES = ["/", "/dashboard", "/table", "/h2h", "/analytics", "/fpl-lab", "/settings", "/reports", "/download"]
API_GET_ROUTES = [
    "/api/v1/health", "/api/v1/teams", "/api/v1/teams/ars", "/api/v1/fixtures",
    "/api/v1/fixtures?matchweek=1", "/api/v1/predict/ars/cov",
    "/api/v1/fpl/captain-picks?matchweek=1", "/api/v1/model/metadata",
]
DOWNLOAD_ROUTES = [
    "/download/fixtures.csv", "/download/predictions.csv?matchweek=1",
    "/download/predictions.xlsx?matchweek=1",
]


@pytest.mark.parametrize("route", PAGE_ROUTES)
def test_page_routes_load(client, route):
    resp = client.get(route)
    assert resp.status_code == 200


@pytest.mark.parametrize("route", API_GET_ROUTES)
def test_api_routes_return_json(client, route):
    resp = client.get(route)
    assert resp.status_code == 200
    assert resp.is_json


@pytest.mark.parametrize("route", DOWNLOAD_ROUTES)
def test_download_routes_return_files(client, route):
    resp = client.get(route)
    assert resp.status_code == 200
    assert len(resp.data) > 0


def test_predict_unknown_team_returns_404(client):
    resp = client.get("/api/v1/predict/xxx/yyy")
    assert resp.status_code == 404


def test_simulate_season_endpoint(client):
    resp = client.post("/api/v1/simulate-season", json={"n_sims": 50})
    assert resp.status_code == 200
    data = resp.get_json()
    assert len(data["projection"]) == 20
    assert data["n_sims"] == 50
