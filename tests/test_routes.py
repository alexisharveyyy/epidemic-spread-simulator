"""Integration tests for the FastAPI routes."""

import re

from app.constants import CSV_OUTPUT_DIR


def test_root_returns_html(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert "EPIDEMIC SPREAD SIMULATOR" in response.text


def test_static_styles_served(client):
    response = client.get("/static/styles.css")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/css")


def test_health_endpoint(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_simulate_default_parameters(client, default_simulation_request):
    response = client.post("/api/simulate", json=default_simulation_request)
    assert response.status_code == 200
    body = response.json()
    assert "records" in body
    assert "summary" in body
    assert "chart_b64" in body
    assert isinstance(body["records"], list)
    assert len(body["records"]) > 0
    assert body["chart_b64"]
    summary = body["summary"]
    for key in (
        "peak_infected",
        "peak_day",
        "total_recovered",
        "outbreak_duration_days",
        "herd_immunity_reached",
    ):
        assert key in summary


def test_simulate_invalid_beta(client, default_simulation_request):
    payload = {**default_simulation_request, "beta": 0.0}
    response = client.post("/api/simulate", json=payload)
    assert response.status_code == 422


def test_simulate_invalid_initial_infected_ge_population(
    client, default_simulation_request
):
    payload = {
        **default_simulation_request,
        "initial_infected": default_simulation_request["population"],
    }
    response = client.post("/api/simulate", json=payload)
    assert response.status_code == 422


def test_simulate_defaults_endpoint(client):
    response = client.get("/api/simulate/defaults")
    assert response.status_code == 200
    body = response.json()
    assert isinstance(body["population"], int)
    assert isinstance(body["beta"], float)
    assert isinstance(body["gamma"], float)
    assert isinstance(body["initial_infected"], int)
    assert isinstance(body["days"], int)
    assert isinstance(body["export_csv"], bool)


def test_simulate_with_csv_export_returns_download_path(
    client, default_simulation_request
):
    payload = {**default_simulation_request, "export_csv": True}
    response = client.post("/api/simulate", json=payload)
    assert response.status_code == 200
    body = response.json()
    path = body["csv_download_path"]
    assert path is not None
    assert re.fullmatch(
        r"/api/simulate/download/simulation_\d{8}_\d{6}\.csv", path
    )
    # Cleanup so we don't litter the dev's data/ directory.
    filename = path.rsplit("/", 1)[-1]
    (CSV_OUTPUT_DIR / filename).unlink(missing_ok=True)


def test_download_missing_file_returns_404(client):
    response = client.get(
        "/api/simulate/download/simulation_19990101_000000.csv"
    )
    assert response.status_code == 404


def test_download_path_traversal_is_blocked(client):
    # URL-encoded `../../etc/passwd`. Either layer can block: the route's
    # filename-pattern regex (400) or Starlette's path normalization that
    # makes the request miss the route entirely (404). Both are effective.
    response = client.get(
        "/api/simulate/download/%2E%2E%2F%2E%2E%2Fetc%2Fpasswd"
    )
    assert response.status_code in (400, 404)
    # And a non-encoded malformed filename must hit the handler's 400 branch.
    bad_name_response = client.get("/api/simulate/download/bogus.csv")
    assert bad_name_response.status_code == 400


def test_csv_download_round_trip(client, default_simulation_request):
    payload = {**default_simulation_request, "export_csv": True}
    response = client.post("/api/simulate", json=payload)
    assert response.status_code == 200
    download_path = response.json()["csv_download_path"]
    filename = download_path.rsplit("/", 1)[-1]
    try:
        download_response = client.get(download_path)
        assert download_response.status_code == 200
        assert download_response.headers["content-type"].startswith("text/csv")
        assert "attachment" in download_response.headers.get(
            "content-disposition", ""
        )
        assert filename in download_response.headers["content-disposition"]
    finally:
        (CSV_OUTPUT_DIR / filename).unlink(missing_ok=True)
