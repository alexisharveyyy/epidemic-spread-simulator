"""SIR simulation routes: run, defaults, and CSV download."""

import logging
import re

from fastapi import APIRouter, HTTPException
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import FileResponse

from app.constants import (
    CSV_OUTPUT_DIR,
    DEFAULT_BETA,
    DEFAULT_EXPORT_CSV,
    DEFAULT_GAMMA,
    DEFAULT_INITIAL_INFECTED,
    DEFAULT_POPULATION,
    DEFAULT_TIME_DAYS,
)
from app.models.request_models import SimulationRequest
from app.models.response_models import (
    SimulationDefaultsResponse,
    SimulationResponse,
)
from app.services.exporter import build_csv_filename, export_to_csv
from app.services.sir_model import compute_summary, run_simulation
from app.services.visualizer import generate_sir_chart

logger = logging.getLogger(__name__)
router = APIRouter()

# Pattern used both to construct download URLs and to validate user input
# coming back through the download endpoint.
_FILENAME_PATTERN = re.compile(r"simulation_\d{8}_\d{6}\.csv")


@router.post("/simulate", response_model=SimulationResponse)
async def simulate(request: SimulationRequest) -> SimulationResponse:
    """Run an SIR simulation and return records, summary, chart, and CSV link."""
    try:
        # `odeint` is CPU-bound; offload to a worker thread to avoid blocking
        # the event loop.
        records = await run_in_threadpool(run_simulation, request)
        summary = compute_summary(
            records, request.beta, request.gamma, request.population
        )
        # matplotlib rendering can take >50ms for large `days` values; offload too.
        chart_b64 = await run_in_threadpool(
            generate_sir_chart,
            records,
            request.population,
            request.beta,
            request.gamma,
        )

        csv_download_path: str | None = None
        if request.export_csv:
            filename = build_csv_filename()
            path = CSV_OUTPUT_DIR / filename
            await run_in_threadpool(export_to_csv, records, path)
            csv_download_path = f"/api/simulate/download/{filename}"
    except ValueError as exc:
        # Covers conservation invariant failures and any explicit ValueError
        # raised from the service layer.
        raise HTTPException(
            status_code=500, detail=f"Simulation failed: {exc}"
        ) from exc

    return SimulationResponse(
        records=records,
        summary=summary,
        chart_b64=chart_b64,
        csv_download_path=csv_download_path,
    )


@router.get("/simulate/defaults", response_model=SimulationDefaultsResponse)
async def simulate_defaults() -> SimulationDefaultsResponse:
    """Return the default simulation parameters for the frontend reset button."""
    return SimulationDefaultsResponse(
        population=DEFAULT_POPULATION,
        beta=DEFAULT_BETA,
        gamma=DEFAULT_GAMMA,
        initial_infected=DEFAULT_INITIAL_INFECTED,
        days=DEFAULT_TIME_DAYS,
        export_csv=DEFAULT_EXPORT_CSV,
    )


@router.get("/simulate/download/{filename}")
async def simulate_download(filename: str) -> FileResponse:
    """Stream a previously generated CSV file by filename.

    The strict filename validation here prevents path traversal attacks
    (e.g., URL-encoded `../../etc/passwd`).
    """
    if not _FILENAME_PATTERN.fullmatch(filename):
        raise HTTPException(status_code=400, detail="Invalid filename format")

    path = CSV_OUTPUT_DIR / filename
    if not path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(
        path=path,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
