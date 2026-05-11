"""Chart generation for the SIR simulation results.

Produces base64-encoded PNG charts and on-disk PNG files using matplotlib.
"""

import base64
import io
import logging
import pathlib

import matplotlib

matplotlib.use("Agg")  # Non-interactive backend required for server-side rendering.
# Without this, matplotlib attempts to open a display window, which raises
# an error in headless server environments.

import matplotlib.pyplot as plt  # noqa: E402

from app.constants import (  # noqa: E402
    CHART_BG_AXES,
    CHART_BG_PRIMARY,
    CHART_COLOR_I,
    CHART_COLOR_LABELS,
    CHART_COLOR_R,
    CHART_COLOR_S,
    CHART_DPI,
    CHART_FIGSIZE,
    CHART_GRID_ALPHA,
)
from app.models.response_models import DailyRecord  # noqa: E402

logger = logging.getLogger(__name__)

# Apply matplotlib rcParams at module level so every chart inherits the
# theme without repeating configuration inside each function.
plt.rcParams.update(
    {
        "figure.facecolor": CHART_BG_PRIMARY,
        "axes.facecolor": CHART_BG_AXES,
        "axes.edgecolor": CHART_COLOR_LABELS,
        "axes.labelcolor": CHART_COLOR_LABELS,
        "xtick.color": CHART_COLOR_LABELS,
        "ytick.color": CHART_COLOR_LABELS,
        "text.color": CHART_COLOR_LABELS,
        "grid.color": CHART_COLOR_LABELS,
        "grid.alpha": CHART_GRID_ALPHA,
        "legend.facecolor": CHART_BG_AXES,
        "legend.edgecolor": CHART_COLOR_LABELS,
    }
)


def _build_figure(
    records: list[DailyRecord],
    population: int,
    beta: float,
    gamma: float,
) -> "plt.Figure":
    """Construct the SIR chart figure (shared between base64 and file output)."""
    days = [r.day for r in records]
    susceptible = [r.susceptible for r in records]
    infected = [r.infected for r in records]
    recovered = [r.recovered for r in records]

    fig, ax = plt.subplots(figsize=CHART_FIGSIZE, dpi=CHART_DPI)
    ax.plot(days, susceptible, color=CHART_COLOR_S, linewidth=2, label="Susceptible")
    ax.plot(days, infected, color=CHART_COLOR_I, linewidth=2, label="Infected")
    ax.plot(days, recovered, color=CHART_COLOR_R, linewidth=2, label="Recovered")

    # Peak infection vertical guide.
    peak_record = max(records, key=lambda r: r.infected)
    ax.axvline(
        x=peak_record.day,
        color=CHART_COLOR_I,
        linestyle="--",
        alpha=0.5,
        label=f"Peak: Day {peak_record.day}",
    )

    # Herd immunity threshold line, only meaningful when R0 > 1.
    r0 = beta / gamma
    if r0 > 1:
        threshold = (1 - 1 / r0) * population
        ax.axhline(
            y=threshold,
            color=CHART_COLOR_S,
            linestyle="--",
            alpha=0.4,
            label="Herd immunity threshold",
        )

    ax.set_xlabel("Days")
    ax.set_ylabel("Individuals")
    ax.grid(True)
    ax.legend(loc="upper right")
    fig.tight_layout()
    return fig


def generate_sir_chart(
    records: list[DailyRecord],
    population: int,
    beta: float,
    gamma: float,
) -> str:
    """Render the SIR chart and return raw base64 PNG (no data: URI prefix)."""
    fig = _build_figure(records, population, beta, gamma)
    buffer = io.BytesIO()
    fig.savefig(buffer, format="png", dpi=CHART_DPI)
    buffer.seek(0)
    encoded = base64.b64encode(buffer.read()).decode("ascii")

    # matplotlib figures must be explicitly closed after base64 encoding.
    # In a long-running FastAPI process, unclosed figures accumulate in memory
    # because matplotlib maintains a global figure registry by default.
    plt.close(fig)
    return encoded


def save_chart_to_file(
    records: list[DailyRecord],
    population: int,
    beta: float,
    gamma: float,
    output_path: pathlib.Path,
) -> None:
    """Render the SIR chart and save it as a PNG to disk."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig = _build_figure(records, population, beta, gamma)
    fig.savefig(output_path, format="png", dpi=CHART_DPI)
    plt.close(fig)
