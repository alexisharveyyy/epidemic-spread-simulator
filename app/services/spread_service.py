"""Geographic spread preview service.

Computes wave rings, secondary clusters, and aggregate spread statistics
for the map UI based on SIR transmission parameters and the current
simulation day.
"""

import logging
from typing import TypedDict

from app.constants import (
    SPREAD_CLUSTER_RAMP_DAYS,
    SPREAD_COUNTRIES_PER_DAY,
    SPREAD_KM_SCALE,
    SPREAD_LAT_CLAMP,
    SPREAD_TOTAL_COUNTRIES,
)
from app.models.request_models import SpreadRequest
from app.models.response_models import (
    SecondaryCluster,
    SpreadResponse,
    SpreadSummary,
    WaveRing,
)

logger = logging.getLogger(__name__)


class SecondaryOffset(TypedDict):
    """Definition of a secondary outbreak cluster relative to the origin."""

    dlat: float
    dlng: float
    scale: float
    threshold: int


SECONDARY_OFFSETS: list[SecondaryOffset] = [
    {"dlat": 12.0, "dlng": 18.0, "scale": 0.55, "threshold": 20},
    {"dlat": -8.0, "dlng": -22.0, "scale": 0.45, "threshold": 25},
    {"dlat": 18.0, "dlng": -15.0, "scale": 0.38, "threshold": 32},
    {"dlat": -14.0, "dlng": 28.0, "scale": 0.50, "threshold": 40},
    {"dlat": 5.0, "dlng": 35.0, "scale": 0.42, "threshold": 50},
]

WAVE_SEVERITY_MAP: dict[int, str] = {
    0: "critical",
    1: "critical",
    2: "moderate",
    3: "early",
}
WAVE_RADIUS_FACTORS: list[float] = [1.0, 1.8, 2.8, 4.2]


def clamp_lat(lat: float) -> float:
    """Clamp a latitude to the visible Mercator range [-80, 80]."""
    return max(-SPREAD_LAT_CLAMP, min(SPREAD_LAT_CLAMP, lat))


def wrap_lng(lng: float) -> float:
    """Wrap a longitude into the [-180, 180) range."""
    return ((lng + 180) % 360) - 180


def compute_base_radius_km(day: int, beta: float, gamma: float) -> float:
    """Return the base spread radius in kilometers for a given day.

    Dividing beta by gamma yields the basic reproduction number R0; scaling
    spread by R0 ties geographic expansion directly to the SIR transmission
    dynamics rather than using an arbitrary fixed rate.
    """
    return day * (beta / gamma) * SPREAD_KM_SCALE


def build_wave_rings(
    origin_lat: float,
    origin_lng: float,
    base_km: float,
    day: int,
) -> list[WaveRing]:
    """Generate up to four concentric wave rings around the origin.

    Number of active waves grows with the simulation day:
        active = min(4, day // 12 + 1)

    Returns an empty list if `day == 0`.
    """
    if day == 0:
        return []

    active = min(4, day // 12 + 1)
    rings: list[WaveRing] = []
    for i in range(active):
        rings.append(
            WaveRing(
                center_lat=clamp_lat(origin_lat),
                center_lng=wrap_lng(origin_lng),
                radius_km=base_km * WAVE_RADIUS_FACTORS[i],
                wave_index=i,
                severity=WAVE_SEVERITY_MAP[i],
            )
        )
    return rings


def build_secondary_clusters(
    origin_lat: float,
    origin_lng: float,
    base_km: float,
    day: int,
) -> list[SecondaryCluster]:
    """Generate secondary clusters that activate after their day threshold.

    Each cluster ramps from radius zero to its full scaled radius linearly
    over `SPREAD_CLUSTER_RAMP_DAYS` days after activation.
    """
    clusters: list[SecondaryCluster] = []
    for offset in SECONDARY_OFFSETS:
        threshold = offset["threshold"]
        if threshold > day:
            continue
        progress = min(1.0, max(0.0, (day - threshold) / SPREAD_CLUSTER_RAMP_DAYS))
        clusters.append(
            SecondaryCluster(
                center_lat=clamp_lat(origin_lat + offset["dlat"]),
                center_lng=wrap_lng(origin_lng + offset["dlng"]),
                radius_km=base_km * offset["scale"] * progress,
                activated_day=threshold,
            )
        )
    return clusters


def compute_spread(request: SpreadRequest) -> SpreadResponse:
    """Orchestrate spread map computation for a single day."""
    # Day-zero short-circuit: nothing has spread yet.
    if request.day == 0:
        return SpreadResponse(
            wave_rings=[],
            secondary_clusters=[],
            summary=SpreadSummary(
                countries_affected=0,
                spread_radius_km=0.0,
                wave_count=0,
                simulation_day=0,
            ),
        )

    base_km = compute_base_radius_km(request.day, request.beta, request.gamma)
    wave_rings = build_wave_rings(
        request.origin_lat, request.origin_lng, base_km, request.day
    )
    secondary_clusters = build_secondary_clusters(
        request.origin_lat, request.origin_lng, base_km, request.day
    )

    # Geometric approximation of exponential international case detection
    # growth, capped at 195 (UN-recognized countries).
    # TODO: Replace with real flight-network graph data so spread maps
    # reflect actual travel connectivity rather than a linear approximation.
    countries_affected = min(
        SPREAD_TOTAL_COUNTRIES,
        int(request.day * SPREAD_COUNTRIES_PER_DAY),
    )

    radii = [r.radius_km for r in wave_rings] + [
        c.radius_km for c in secondary_clusters
    ]
    spread_radius_km = max(radii) if radii else 0.0

    return SpreadResponse(
        wave_rings=wave_rings,
        secondary_clusters=secondary_clusters,
        summary=SpreadSummary(
            countries_affected=countries_affected,
            spread_radius_km=spread_radius_km,
            wave_count=len(wave_rings),
            simulation_day=request.day,
        ),
    )
