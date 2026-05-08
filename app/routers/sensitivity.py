"""Sensitivity analysis sweep router."""

import logging

from fastapi import APIRouter, HTTPException
from fastapi.concurrency import run_in_threadpool

from app.models.request_models import SensitivityRequest
from app.models.response_models import SensitivityRunResponse
from app.services import sensitivity_service

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/sensitivity/run", response_model=SensitivityRunResponse)
async def run_sensitivity(request: SensitivityRequest) -> SensitivityRunResponse:
    """Run a parameter sweep and return per-point summaries plus a chart.

    The sweep solves the SIR ODE up to 50 times, so it is offloaded to a
    worker thread to avoid blocking the event loop.
    """
    try:
        return await run_in_threadpool(sensitivity_service.run_sweep, request)
    except ValueError as exc:
        # Cross-field "too many points" check; field-level validation already
        # passed at this point, so 400 (not 422) is the correct status.
        raise HTTPException(status_code=400, detail=str(exc)) from exc
