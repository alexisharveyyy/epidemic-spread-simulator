"""Pydantic v2 response models for the epidemic simulator API."""

from pydantic import BaseModel, ConfigDict


class DailyRecord(BaseModel):
    """One day's snapshot of the SIR compartments plus effective Rt.

    `rt` is the effective reproduction number at the timestep:
    `Rt = (beta * S(t)) / (gamma * N)`. Distinct from `R0 = beta / gamma`
    (basic reproduction number assuming full susceptibility at t=0); Rt
    declines over time as S(t) decreases, and Rt < 1 marks the turning
    point after which daily new infections begin to fall.
    """

    day: int
    susceptible: float
    infected: float
    recovered: float
    rt: float

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "day": 0,
                "susceptible": 99990.0,
                "infected": 10.0,
                "recovered": 0.0,
                "rt": 2.999,
            }
        }
    )


class SimulationSummary(BaseModel):
    """Aggregate epidemiological metrics derived from a full record series."""

    peak_infected: int
    peak_day: int
    total_recovered: int
    outbreak_duration_days: int
    herd_immunity_reached: bool


class SimulationResponse(BaseModel):
    """Full simulation result envelope.

    `chart_b64` is the raw base64 PNG payload, WITHOUT the
    `data:image/png;base64,` URI prefix. The frontend constructs the
    data URI on the client side.
    """

    records: list[DailyRecord]
    summary: SimulationSummary
    chart_b64: str
    csv_download_path: str | None = None


class SimulationDefaultsResponse(BaseModel):
    """Default simulation parameters returned by GET /api/simulate/defaults."""

    population: int
    beta: float
    gamma: float
    initial_infected: int
    days: int
    export_csv: bool


class HealthResponse(BaseModel):
    """Liveness probe response."""

    status: str


class NewsArticle(BaseModel):
    """One outbreak intelligence headline."""

    headline: str
    source: str
    severity: str  # "critical", "moderate", or "watch"
    time: str  # human-readable relative string, e.g. "12m ago"
    url: str | None = None


class WaveRing(BaseModel):
    """A circular ring on the spread map representing one wave of infection."""

    center_lat: float
    center_lng: float
    radius_km: float
    wave_index: int
    severity: str  # "critical", "moderate", or "early"


class SecondaryCluster(BaseModel):
    """A secondary outbreak cluster activated after a threshold day."""

    center_lat: float
    center_lng: float
    radius_km: float
    activated_day: int


class SpreadSummary(BaseModel):
    """Summary statistics for the geographic spread preview."""

    countries_affected: int
    spread_radius_km: float
    wave_count: int
    simulation_day: int


class SpreadResponse(BaseModel):
    """Full spread map preview response."""

    wave_rings: list[WaveRing]
    secondary_clusters: list[SecondaryCluster]
    summary: SpreadSummary


class Scenario(BaseModel):
    """One pre-configured disease parameter set in the scenario library."""

    id: str
    name: str
    description: str
    beta: float
    gamma: float
    initial_infected: int
    population: int
    days: int
    expected_outcome: str


class ScenarioListResponse(BaseModel):
    """Wrapper around the full scenario library."""

    scenarios: list[Scenario]


class SensitivityPoint(BaseModel):
    """One row of the sensitivity-analysis sweep result table."""

    parameter_value: float
    peak_infected: int
    peak_day: int
    total_recovered: int
    outbreak_duration_days: int


class SensitivityRunResponse(BaseModel):
    """Sensitivity sweep envelope.

    `chart_b64` is the raw base64 PNG payload, WITHOUT the
    `data:image/png;base64,` URI prefix. The frontend constructs the
    data URI on the client side.
    """

    sweep_parameter: str
    points: list[SensitivityPoint]
    chart_b64: str
