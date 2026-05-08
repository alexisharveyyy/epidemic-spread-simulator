"""Scenario library API routes."""

import logging

from fastapi import APIRouter, HTTPException

from app.models.response_models import Scenario, ScenarioListResponse
from app.services import scenario_service

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/scenarios", response_model=ScenarioListResponse)
async def list_scenarios_endpoint() -> ScenarioListResponse:
    """Return the full scenario library."""
    return ScenarioListResponse(scenarios=scenario_service.list_scenarios())


@router.get("/scenarios/{scenario_id}", response_model=Scenario)
async def get_scenario_endpoint(scenario_id: str) -> Scenario:
    """Fetch a single scenario by ID, 404 if not found."""
    scenario = scenario_service.get_scenario(scenario_id)
    if scenario is None:
        raise HTTPException(status_code=404, detail="Scenario not found")
    return scenario
