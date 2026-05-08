"""Geographic spread preview router."""

import logging

from fastapi import APIRouter, HTTPException

from app.models.request_models import SpreadRequest
from app.models.response_models import SpreadResponse
from app.services import spread_service

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/spread/preview", response_model=SpreadResponse)
async def spread_preview(request: SpreadRequest) -> SpreadResponse:
    """Compute wave rings and secondary clusters for the given simulation day."""
    try:
        return spread_service.compute_spread(request)
    except Exception as exc:
        # Pydantic handles 422s for invalid input shape; this catches any
        # unexpected service-level failure so we return a structured 500.
        raise HTTPException(
            status_code=500, detail=f"Spread computation failed: {exc}"
        ) from exc
