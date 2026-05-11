"""Application-wide constants for the epidemic spread simulator.

All named constants used across simulation, visualization, news, and spread
services live in this module. No magic numbers should appear in any other
file in the codebase.
"""

import pathlib

# ---------------------------------------------------------------------------
# Simulation defaults and bounds
# ---------------------------------------------------------------------------
DEFAULT_POPULATION = 100_000
DEFAULT_BETA = 0.30
DEFAULT_GAMMA = 0.10
DEFAULT_INITIAL_INFECTED = 10
DEFAULT_TIME_DAYS = 160
DEFAULT_EXPORT_CSV = False
MAX_POPULATION = 10_000_000
MAX_DAYS = 365

# ---------------------------------------------------------------------------
# Output paths and chart export
# ---------------------------------------------------------------------------
# Resolve relative to the project root (parent of `app/`) so the output dir
# is `epidemic-simulator/data/` regardless of the working directory at startup.
PROJECT_ROOT = pathlib.Path(__file__).parent.parent
CSV_OUTPUT_DIR = PROJECT_ROOT / "data"
CHART_DPI = 110
CHART_FIGSIZE = (
    10.0,
    5.0,
)  # width, height in inches; renders cleanly inside the 820px UI panel

# ---------------------------------------------------------------------------
# Chart theme constants (must match styles.css palette exactly)
# ---------------------------------------------------------------------------
CHART_BG_PRIMARY = "#0f1628"
CHART_BG_AXES = "#161d35"
CHART_COLOR_LABELS = "#8899bb"
CHART_COLOR_S = "#00d4ff"  # accent-cyan
CHART_COLOR_I = "#ffaa00"  # accent-amber
CHART_COLOR_R = "#00ff88"  # accent-green
CHART_GRID_ALPHA = 0.1

# ---------------------------------------------------------------------------
# News service constants
# ---------------------------------------------------------------------------
NEWS_API_BASE_URL = "https://newsapi.org/v2/everything"
NEWS_TIMEOUT_CONNECT = 3.0
NEWS_TIMEOUT_READ = 5.0
NEWS_PAGE_SIZE = 12
NEWS_QUERY = "outbreak OR epidemic OR pathogen OR disease"

# Note: a `from` (lookback date) parameter is intentionally NOT sent to NewsAPI.
# The free NewsAPI tier rejects requests that specify `from` for dates older than
# 24 hours with HTTP 426 (Upgrade Required), and recent results are returned by
# default without it. This keeps the project usable on the free tier.

# ---------------------------------------------------------------------------
# Spread service constants
# ---------------------------------------------------------------------------
SPREAD_KM_SCALE = 45.0
SPREAD_MAX_DAY = 90
SPREAD_LAT_CLAMP = 80.0
SPREAD_TOTAL_COUNTRIES = 195
SPREAD_COUNTRIES_PER_DAY = 2.1
SPREAD_CLUSTER_RAMP_DAYS = (
    40.0  # days over which a secondary cluster ramps from 0 to full radius
)

# ---------------------------------------------------------------------------
# HTML slider bounds (passed into Jinja2 context so the template never hardcodes them)
# ---------------------------------------------------------------------------
SLIDER_POPULATION_MIN = 1_000
SLIDER_POPULATION_STEP = 1_000

SLIDER_BETA_MIN = 0.05
SLIDER_BETA_MAX = 0.95
SLIDER_BETA_STEP = 0.01

SLIDER_GAMMA_MIN = 0.01
SLIDER_GAMMA_MAX = 0.50
SLIDER_GAMMA_STEP = 0.01

SLIDER_INITIAL_INFECTED_MIN = 1
SLIDER_INITIAL_INFECTED_MAX = 1_000
SLIDER_INITIAL_INFECTED_STEP = 1

SLIDER_DAYS_MIN = 30
SLIDER_DAYS_STEP = 1

# ---------------------------------------------------------------------------
# Sensitivity analysis
# ---------------------------------------------------------------------------
SENSITIVITY_SWEEP_MAX_POINTS = 50
SENSITIVITY_DEFAULT_STEP = 0.025
SENSITIVITY_DEFAULT_FROM = 0.10
SENSITIVITY_DEFAULT_TO = 0.50

# ---------------------------------------------------------------------------
# Vaccination scenarios
# ---------------------------------------------------------------------------
# Cap below 100 since 100% vaccination trivially prevents any outbreak and the
# comparison chart degenerates to a flat line at zero.
VACCINATION_COVERAGE_MAX = 95

# ---------------------------------------------------------------------------
# Conservation tolerance
# ---------------------------------------------------------------------------
# Floating-point tolerance for the S+I+R=N invariant check in run_simulation.
# Scales with population size since absolute error in odeint scales with magnitude.
CONSERVATION_TOLERANCE_FACTOR = 1e-6
