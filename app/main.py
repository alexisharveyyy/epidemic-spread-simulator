"""FastAPI application entry point for the epidemic spread simulator."""

# `load_dotenv()` must run before any other module reads environment variables,
# so this is the very first executable statement in the application.
from dotenv import load_dotenv

load_dotenv()

import logging  # noqa: E402

# `force=True` ensures this configuration takes effect even if uvicorn or
# another process pre-configured the root logger.
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    force=True,
)

from fastapi import FastAPI, Request  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402
from fastapi.responses import HTMLResponse  # noqa: E402
from fastapi.staticfiles import StaticFiles  # noqa: E402

from app.constants import (  # noqa: E402
    CSV_OUTPUT_DIR,
    DEFAULT_BETA,
    DEFAULT_GAMMA,
    DEFAULT_INITIAL_INFECTED,
    DEFAULT_POPULATION,
    DEFAULT_TIME_DAYS,
    MAX_DAYS,
    MAX_POPULATION,
    SLIDER_BETA_MAX,
    SLIDER_BETA_MIN,
    SLIDER_BETA_STEP,
    SLIDER_DAYS_MIN,
    SLIDER_DAYS_STEP,
    SLIDER_GAMMA_MAX,
    SLIDER_GAMMA_MIN,
    SLIDER_GAMMA_STEP,
    SLIDER_INITIAL_INFECTED_MAX,
    SLIDER_INITIAL_INFECTED_MIN,
    SLIDER_INITIAL_INFECTED_STEP,
    SLIDER_POPULATION_MIN,
    SLIDER_POPULATION_STEP,
    SPREAD_MAX_DAY,
)
from app.routers import (  # noqa: E402
    health,
    news,
    pages,
    scenarios,
    sensitivity,
    simulation,
    spread_map,
)
from app.templates_shared import templates  # noqa: E402

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Epidemic Spread Simulator",
    version="1.0.0",
    description=(
        "FastAPI service that runs SIR (Susceptible-Infected-Recovered) "
        "compartmental simulations, generates dark-themed visualizations, "
        "fetches outbreak intelligence headlines, and previews geographic "
        "spread on an interactive map."
    ),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    # `allow_credentials=False` is required when `allow_origins=["*"]`.
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(simulation.router, prefix="/api")
app.include_router(health.router, prefix="/api")
app.include_router(news.router, prefix="/api")
app.include_router(spread_map.router, prefix="/api")
app.include_router(scenarios.router, prefix="/api")
app.include_router(sensitivity.router, prefix="/api")
# Page routes have no /api prefix; they render server-side templates.
app.include_router(pages.router)


@app.on_event("startup")
async def _on_startup() -> None:
    """Ensure the CSV output directory exists and announce server readiness."""
    CSV_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    logger.info("Epidemic Simulator ready - serving on http://127.0.0.1:8000")


@app.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
    """Render the single-page HTML interface with all slider bounds injected."""
    context = {
        "active_page": "home",
        "default_population": DEFAULT_POPULATION,
        "default_beta": DEFAULT_BETA,
        "default_gamma": DEFAULT_GAMMA,
        "default_initial_infected": DEFAULT_INITIAL_INFECTED,
        "default_days": DEFAULT_TIME_DAYS,
        "slider_population_min": SLIDER_POPULATION_MIN,
        "slider_population_max": MAX_POPULATION,
        "slider_population_step": SLIDER_POPULATION_STEP,
        "slider_beta_min": SLIDER_BETA_MIN,
        "slider_beta_max": SLIDER_BETA_MAX,
        "slider_beta_step": SLIDER_BETA_STEP,
        "slider_gamma_min": SLIDER_GAMMA_MIN,
        "slider_gamma_max": SLIDER_GAMMA_MAX,
        "slider_gamma_step": SLIDER_GAMMA_STEP,
        "slider_initial_infected_min": SLIDER_INITIAL_INFECTED_MIN,
        "slider_initial_infected_max": SLIDER_INITIAL_INFECTED_MAX,
        "slider_initial_infected_step": SLIDER_INITIAL_INFECTED_STEP,
        "slider_days_min": SLIDER_DAYS_MIN,
        "slider_days_max": MAX_DAYS,
        "slider_days_step": SLIDER_DAYS_STEP,
        "spread_max_day": SPREAD_MAX_DAY,
    }
    # Modern Starlette signature: request is the first positional argument.
    return templates.TemplateResponse(request, "index.html", context)
