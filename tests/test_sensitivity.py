"""Tests for the sensitivity analysis service and endpoint."""

import base64


def _payload(**overrides) -> dict:
    base = {
        "sweep_parameter": "beta",
        "sweep_from": 0.10,
        "sweep_to": 0.40,
        "step": 0.05,
        "population": 100_000,
        "beta": 0.30,
        "gamma": 0.10,
        "initial_infected": 10,
        "days": 160,
    }
    base.update(overrides)
    return base


def test_run_sweep_happy_path(client):
    response = client.post("/api/sensitivity/run", json=_payload())
    assert response.status_code == 200
    body = response.json()
    # Expected sweep: 0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40 -> 7 points.
    assert body["sweep_parameter"] == "beta"
    assert len(body["points"]) == 7
    assert all(p["peak_infected"] >= 0 for p in body["points"])


def test_run_sweep_chart_is_valid_png(client):
    response = client.post("/api/sensitivity/run", json=_payload())
    chart_b64 = response.json()["chart_b64"]
    assert chart_b64
    decoded = base64.b64decode(chart_b64)
    assert decoded.startswith(b"\x89PNG")


def test_increasing_beta_sweep_produces_non_decreasing_peak(client):
    response = client.post("/api/sensitivity/run", json=_payload())
    peaks = [p["peak_infected"] for p in response.json()["points"]]
    # With gamma fixed at 0.10 and beta sweeping 0.10 -> 0.40, R0 grows
    # monotonically and so does the peak. Allow strict non-decrease.
    for prev, curr in zip(peaks[:-1], peaks[1:]):
        assert curr >= prev, f"Peak dropped from {prev} to {curr}"


def test_run_sweep_invalid_parameter_returns_422(client):
    payload = _payload(sweep_parameter="invalid")
    response = client.post("/api/sensitivity/run", json=payload)
    assert response.status_code == 422


def test_run_sweep_inverted_range_returns_422(client):
    payload = _payload(sweep_from=0.40, sweep_to=0.10)
    response = client.post("/api/sensitivity/run", json=payload)
    assert response.status_code == 422


def test_run_sweep_too_many_points_returns_400(client):
    # 0.01 -> 0.99 step 0.01 yields ~99 points, well above the 50 limit.
    payload = _payload(sweep_from=0.01, sweep_to=0.99, step=0.01)
    response = client.post("/api/sensitivity/run", json=payload)
    assert response.status_code == 400
    detail = response.json()["detail"]
    assert "maximum is 50" in detail or "50" in detail
