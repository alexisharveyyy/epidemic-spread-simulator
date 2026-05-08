"""Sensitivity analysis: parameter sweeps over `beta` or `gamma`.

Runs the SIR model across a range of values for one parameter while
holding all others fixed, and produces both a tabular `points` list
and a base64 PNG chart.
"""

import base64
import io
import logging

import matplotlib.pyplot as plt
import numpy as np

from app.constants import (
    CHART_COLOR_I,
    CHART_COLOR_LABELS,
    CHART_COLOR_R,
    CHART_COLOR_S,
    CHART_DPI,
    CHART_FIGSIZE,
    SENSITIVITY_SWEEP_MAX_POINTS,
)
from app.models.request_models import SensitivityRequest, SimulationRequest
from app.models.response_models import SensitivityPoint, SensitivityRunResponse
from app.services.sir_model import compute_summary, run_simulation

logger = logging.getLogger(__name__)


def run_sweep(request: SensitivityRequest) -> SensitivityRunResponse:
    """Sweep one parameter and return per-point summaries plus a chart."""
    # `sweep_to + step / 2` makes the upper bound inclusive in the face of
    # floating-point rounding (e.g., 0.10 + 0.05 * 6 = 0.4 might land at
    # 0.39999... and be excluded by np.arange without the half-step nudge).
    values = np.arange(
        request.sweep_from,
        request.sweep_to + request.step / 2,
        request.step,
    )

    if len(values) > SENSITIVITY_SWEEP_MAX_POINTS:
        # This is a cross-field check that Pydantic field validators cannot
        # express, so it surfaces as a 400 from the router (not a 422).
        raise ValueError(
            f"Sweep produces {len(values)} points; maximum is "
            f"{SENSITIVITY_SWEEP_MAX_POINTS}. Increase step size."
        )

    points: list[SensitivityPoint] = []
    for value in values:
        sim_kwargs = {
            "population": request.population,
            "beta": request.beta,
            "gamma": request.gamma,
            "initial_infected": request.initial_infected,
            "days": request.days,
            "export_csv": False,
        }
        sim_kwargs[request.sweep_parameter] = float(value)
        sim_request = SimulationRequest(**sim_kwargs)
        records = run_simulation(sim_request)
        summary = compute_summary(
            records,
            sim_request.beta,
            sim_request.gamma,
            sim_request.population,
        )
        points.append(
            SensitivityPoint(
                parameter_value=float(value),
                peak_infected=summary.peak_infected,
                peak_day=summary.peak_day,
                total_recovered=summary.total_recovered,
                outbreak_duration_days=summary.outbreak_duration_days,
            )
        )

    return SensitivityRunResponse(
        sweep_parameter=request.sweep_parameter,
        points=points,
        chart_b64=generate_sensitivity_chart(points, request.sweep_parameter),
    )


def generate_sensitivity_chart(
    points: list[SensitivityPoint], sweep_parameter: str
) -> str:
    """Render a multi-axis sweep chart and return raw base64 PNG."""
    xs = [p.parameter_value for p in points]
    peaks = [p.peak_infected for p in points]
    peak_days = [p.peak_day for p in points]
    totals = [p.total_recovered for p in points]

    fig, ax_left = plt.subplots(figsize=CHART_FIGSIZE, dpi=CHART_DPI)
    ax_right = ax_left.twinx()
    # Match the right-axis tick / label color to the dark theme; matplotlib's
    # twin-axis colors are not inherited from rcParams.
    ax_right.tick_params(axis="y", colors=CHART_COLOR_LABELS)
    ax_right.spines["right"].set_color(CHART_COLOR_LABELS)

    ax_left.plot(xs, peaks, color=CHART_COLOR_S, linewidth=2, label="Peak infected")
    ax_left.plot(xs, totals, color=CHART_COLOR_R, linewidth=2, label="Total recovered")
    ax_right.plot(xs, peak_days, color=CHART_COLOR_I, linewidth=2, label="Peak day")

    pretty = {"beta": r"$\beta$", "gamma": r"$\gamma$"}.get(
        sweep_parameter, sweep_parameter
    )
    ax_left.set_xlabel(f"Sweep over {pretty}")
    ax_left.set_ylabel("Individuals (peak / total)")
    ax_right.set_ylabel("Peak day")
    ax_left.grid(True)

    # Combine the two axes' legends into one box so the user can read it.
    lines_left, labels_left = ax_left.get_legend_handles_labels()
    lines_right, labels_right = ax_right.get_legend_handles_labels()
    ax_left.legend(
        lines_left + lines_right,
        labels_left + labels_right,
        loc="upper right",
    )

    fig.tight_layout()
    buffer = io.BytesIO()
    fig.savefig(buffer, format="png", dpi=CHART_DPI)
    buffer.seek(0)
    encoded = base64.b64encode(buffer.read()).decode("ascii")
    plt.close(fig)
    return encoded
