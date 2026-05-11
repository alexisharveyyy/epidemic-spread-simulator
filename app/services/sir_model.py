"""SIR compartmental model service.

Reference: Kermack & McKendrick (1927), "A Contribution to the Mathematical
Theory of Epidemics", Proc. R. Soc. Lond. A, 115, 700-721.
"""

import logging

import numpy as np
from scipy.integrate import odeint

from app.constants import CONSERVATION_TOLERANCE_FACTOR
from app.models.request_models import SimulationRequest
from app.models.response_models import DailyRecord, SimulationSummary

logger = logging.getLogger(__name__)


def sir_ode(
    y: list[float],
    t: float,
    beta: float,
    gamma: float,
    population: int,
) -> list[float]:
    """SIR differential equation system.

    Args:
        y: State vector [S, I, R].
        t: Time (unused; required by `odeint` signature).
        beta: Transmission rate per S-I contact per unit time.
        gamma: Recovery rate (inverse of mean infectious period).
        population: Total population N (held constant).

    Returns:
        Derivative vector [dS/dt, dI/dt, dR/dt].

    From Kermack & McKendrick (1927), Proc. R. Soc. Lond. A, 115, 700-721:
        dS/dt = -beta * S * I / N
        dI/dt =  beta * S * I / N - gamma * I
        dR/dt =  gamma * I
    """
    susceptible, infected, _recovered = y
    d_susceptible = -beta * susceptible * infected / population
    d_infected = beta * susceptible * infected / population - gamma * infected
    d_recovered = gamma * infected
    return [d_susceptible, d_infected, d_recovered]


def run_simulation(request: SimulationRequest) -> list[DailyRecord]:
    """Integrate the SIR ODE system and return per-day records.

    `odeint` is CPU-bound and synchronous. The FastAPI route handler is
    responsible for wrapping calls in `await run_in_threadpool(...)` to
    avoid blocking the event loop.

    Args:
        request: Validated simulation parameters.

    Returns:
        One `DailyRecord` per integer day from 0 to `request.days` inclusive
        (length = `request.days + 1`).

    Raises:
        ValueError: If the population conservation invariant
            (S + I + R == N) is violated at any timestep.
    """
    population = request.population
    initial_infected = request.initial_infected
    # `initial_recovered` lets the vaccination scenario start a fraction of the
    # population in the immune compartment (a common steady-state-vaccination
    # approximation; full vaccination dynamics would require an SIRV model).
    initial_recovered = request.initial_recovered
    initial_susceptible = population - initial_infected - initial_recovered
    y0 = [initial_susceptible, initial_infected, initial_recovered]

    # Exactly one sample per day, inclusive of both endpoints, producing
    # `days + 1` records.
    t = np.linspace(0, request.days, request.days + 1)

    solution = odeint(
        sir_ode,
        y0,
        t,
        args=(request.beta, request.gamma, population),
    )

    tolerance = CONSERVATION_TOLERANCE_FACTOR * population
    records: list[DailyRecord] = []
    for i, day in enumerate(t):
        s_t, i_t, r_t = solution[i]
        actual = s_t + i_t + r_t
        if abs(actual - population) >= tolerance:
            raise ValueError(
                f"Population conservation violated at day {day}: "
                f"sum={actual:.2f}, expected={population}"
            )

        # Per-timestep effective reproduction number.
        # Distinct from R0 = beta / gamma (basic reproduction number,
        # constant, computed once); Rt declines over time as S falls.
        rt = (request.beta * s_t) / (request.gamma * population)

        records.append(
            DailyRecord(
                day=int(day),
                susceptible=float(s_t),
                infected=float(i_t),
                recovered=float(r_t),
                rt=float(rt),
            )
        )

    return records


def compute_summary(
    records: list[DailyRecord],
    beta: float,
    gamma: float,
    population: int,
) -> SimulationSummary:
    """Derive aggregate epidemiological metrics from a record series.

    Pure function with no scipy or solver dependencies.

    Herd immunity threshold formula: `1 - 1/R0`. When R0 <= 1, no meaningful
    threshold exists and `herd_immunity_reached` is False.
    """
    peak_infected = int(round(max(r.infected for r in records)))
    peak_day = int(max(records, key=lambda r: r.infected).day)
    total_recovered = int(round(records[-1].recovered))
    # Count of days where active infections exceed 1 individual.
    outbreak_duration_days = sum(1 for r in records if r.infected > 1.0)

    r0 = beta / gamma
    if r0 <= 1:
        # No outbreak threshold exists; the disease dies out without herd immunity.
        herd_immunity_reached = False
    else:
        threshold = (1 - 1 / r0) * population
        herd_immunity_reached = bool(max(r.recovered for r in records) >= threshold)

    return SimulationSummary(
        peak_infected=peak_infected,
        peak_day=peak_day,
        total_recovered=total_recovered,
        outbreak_duration_days=outbreak_duration_days,
        herd_immunity_reached=herd_immunity_reached,
    )
