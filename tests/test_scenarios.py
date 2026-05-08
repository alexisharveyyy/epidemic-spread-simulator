"""Tests for the scenario library service and API."""

from app.services.scenario_service import get_scenario, list_scenarios


def test_list_scenarios_endpoint(client):
    response = client.get("/api/scenarios")
    assert response.status_code == 200
    body = response.json()
    assert "scenarios" in body
    assert isinstance(body["scenarios"], list)
    assert len(body["scenarios"]) > 0


def test_every_scenario_has_required_fields(client):
    response = client.get("/api/scenarios")
    for scenario in response.json()["scenarios"]:
        for field in (
            "id",
            "name",
            "description",
            "beta",
            "gamma",
            "initial_infected",
            "population",
            "days",
            "expected_outcome",
        ):
            assert scenario[field] not in (None, "", 0) or field in {"initial_infected"}, (
                f"Scenario {scenario.get('id')} missing/empty field {field}"
            )


def test_every_scenario_has_positive_r0(client):
    for scenario in client.get("/api/scenarios").json()["scenarios"]:
        assert scenario["beta"] / scenario["gamma"] > 0


def test_get_scenario_by_id(client):
    response = client.get("/api/scenarios/measles_unvaccinated")
    assert response.status_code == 200
    body = response.json()
    assert body["id"] == "measles_unvaccinated"
    assert "MEASLES" in body["name"]


def test_get_scenario_unknown_returns_404(client):
    response = client.get("/api/scenarios/nonexistent_id")
    assert response.status_code == 404
    assert response.json() == {"detail": "Scenario not found"}


def test_list_scenarios_returns_at_least_six():
    assert len(list_scenarios()) >= 6


def test_get_scenario_helper_returns_object_or_none():
    assert get_scenario("measles_unvaccinated") is not None
    assert get_scenario("bogus") is None
