"""Scenario library: pre-configured disease parameter sets.

Expected outcome strings are static labels; the actual simulation may
differ slightly because they are not recomputed at request time. They
exist to give the user an at-a-glance preview of what each scenario
produces without running it.
"""

from app.models.response_models import Scenario

SCENARIO_LIBRARY: list[Scenario] = [
    Scenario(
        id="measles_unvaccinated",
        name="MEASLES — UNVACCINATED POPULATION",
        description=(
            "One of the most contagious human diseases. Before widespread "
            "vaccination, measles caused recurring outbreaks with rapid "
            "spread among children."
        ),
        beta=0.90,
        gamma=0.07,
        initial_infected=5,
        population=100_000,
        days=160,
        expected_outcome="Peak infected: ~78% · Peak day: ~28 · Herd immunity: 92%",
    ),
    Scenario(
        id="covid_original",
        name="COVID-19 — ORIGINAL STRAIN",
        description=(
            "The Wuhan-strain SARS-CoV-2 in early 2020 before vaccines and "
            "variants. Used here as a parameter benchmark, not an "
            "epidemiological forecast."
        ),
        beta=0.35,
        gamma=0.10,
        initial_infected=10,
        population=100_000,
        days=200,
        expected_outcome="Peak infected: ~28% · Peak day: ~58 · Herd immunity: 71%",
    ),
    Scenario(
        id="seasonal_flu",
        name="SEASONAL INFLUENZA",
        description=(
            "A typical seasonal influenza strain with moderate "
            "transmissibility and short infectious period."
        ),
        beta=0.20,
        gamma=0.15,
        initial_infected=20,
        population=100_000,
        days=120,
        expected_outcome="Peak infected: ~5% · Peak day: ~50 · Herd immunity: 25%",
    ),
    Scenario(
        id="common_cold",
        name="COMMON COLD (RHINOVIRUS)",
        description=(
            "Rhinoviruses spread efficiently but recovery is fast. Most "
            "outbreaks burn out without reaching a large fraction of the "
            "population."
        ),
        beta=0.25,
        gamma=0.30,
        initial_infected=30,
        population=100_000,
        days=90,
        expected_outcome=(
            "Peak infected: <2% · Peak day: minimal · Outbreak self-limits"
        ),
    ),
    Scenario(
        id="ebola",
        name="EBOLA — UNCONTAINED",
        description=(
            "A severe outbreak with low R0 but very high case-fatality. "
            "Recovery is slow; this scenario assumes no intervention."
        ),
        beta=0.15,
        gamma=0.05,
        initial_infected=3,
        population=50_000,
        days=300,
        expected_outcome="Peak infected: ~26% · Peak day: ~110 · Herd immunity: 67%",
    ),
    Scenario(
        id="pertussis",
        name="PERTUSSIS (WHOOPING COUGH)",
        description=(
            "Highly contagious bacterial respiratory disease. Vaccination "
            "has reduced incidence dramatically; this scenario shows "
            "unmitigated spread."
        ),
        beta=0.55,
        gamma=0.10,
        initial_infected=10,
        population=100_000,
        days=180,
        expected_outcome="Peak infected: ~50% · Peak day: ~45 · Herd immunity: 82%",
    ),
]


def list_scenarios() -> list[Scenario]:
    """Return every scenario in the library, in declared order."""
    return SCENARIO_LIBRARY


def get_scenario(scenario_id: str) -> Scenario | None:
    """Return the scenario matching `scenario_id`, or `None` if no match."""
    for scenario in SCENARIO_LIBRARY:
        if scenario.id == scenario_id:
            return scenario
    return None
