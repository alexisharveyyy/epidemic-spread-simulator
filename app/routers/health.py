"""Liveness probe router."""

from fastapi import APIRouter

from app.models.response_models import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """Return a simple `{status: "ok"}` payload for deployment health checks."""
    return HealthResponse(status="ok")
