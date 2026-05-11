"""Tests for the geographic spread preview."""

from app.services.spread_service import compute_base_radius_km, wrap_lng


def test_spread_preview_returns_wave_rings(client, default_spread_request):
    response = client.post("/api/spread/preview", json=default_spread_request)
    assert response.status_code == 200
    body = response.json()
    assert len(body["wave_rings"]) >= 1


def test_base_radius_doubles_when_beta_doubles():
    r1 = compute_base_radius_km(day=30, beta=0.3, gamma=0.1)
    r2 = compute_base_radius_km(day=30, beta=0.6, gamma=0.1)
    assert abs(r2 - 2 * r1) < 1e-6


def test_base_radius_doubles_when_gamma_halves():
    r1 = compute_base_radius_km(day=30, beta=0.3, gamma=0.1)
    r2 = compute_base_radius_km(day=30, beta=0.3, gamma=0.05)
    assert abs(r2 - 2 * r1) < 1e-6


def test_latitude_clamped_to_visible_range(client):
    response = client.post(
        "/api/spread/preview",
        json={
            "origin_lat": 85,
            "origin_lng": 0,
            "day": 30,
            "beta": 0.3,
            "gamma": 0.1,
        },
    )
    # Pydantic accepts 85 (within [-90, 90]) but service clamps to 80.
    assert response.status_code == 200
    body = response.json()
    for ring in body["wave_rings"]:
        assert ring["center_lat"] == 80


def test_wrap_lng_handles_overflow():
    assert wrap_lng(200) == -160


def test_secondary_clusters_empty_when_day_under_20(client, default_spread_request):
    payload = {**default_spread_request, "day": 10}
    response = client.post("/api/spread/preview", json=payload)
    assert response.status_code == 200
    assert response.json()["secondary_clusters"] == []


def test_secondary_clusters_present_when_day_at_least_20(
    client, default_spread_request
):
    payload = {**default_spread_request, "day": 25}
    response = client.post("/api/spread/preview", json=payload)
    assert response.status_code == 200
    assert len(response.json()["secondary_clusters"]) >= 1


def test_day_zero_returns_empty_response(client, default_spread_request):
    payload = {**default_spread_request, "day": 0}
    response = client.post("/api/spread/preview", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body["wave_rings"] == []
    assert body["secondary_clusters"] == []
    assert body["summary"]["countries_affected"] == 0
    assert body["summary"]["spread_radius_km"] == 0.0
    assert body["summary"]["wave_count"] == 0
    assert body["summary"]["simulation_day"] == 0


def test_invalid_origin_lat_returns_422(client, default_spread_request):
    payload = {**default_spread_request, "origin_lat": 200}
    response = client.post("/api/spread/preview", json=payload)
    assert response.status_code == 422


def test_day_above_max_returns_422(client, default_spread_request):
    payload = {**default_spread_request, "day": 100}
    response = client.post("/api/spread/preview", json=payload)
    assert response.status_code == 422
