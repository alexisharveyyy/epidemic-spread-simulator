"""Unit tests for the SIR model service."""

import numpy as np
import pytest

from app.models.request_models import SimulationRequest
from app.services.sir_model import compute_summary, run_simulation


def _make_request(**overrides) -> SimulationRequest:
    base = {
        "population": 100_000,
        "beta": 0.3,
        "gamma": 0.1,
        "initial_infected": 10,
        "days": 160,
        "export_csv": False,
    }
    base.update(overrides)
    return SimulationRequest(**base)


def test_population_conservation():
    request = _make_request()
    records = run_simulation(request)
    for r in records:
        assert abs(r.susceptible + r.infected + r.recovered - request.population) < 1.0


def test_susceptible_monotonically_non_increasing():
    records = run_simulation(_make_request())
    susceptibles = [r.susceptible for r in records]
    for prev, curr in zip(susceptibles[:-1], susceptibles[1:]):
        assert curr <= prev + 1e-6


def test_recovered_monotonically_non_decreasing():
    records = run_simulation(_make_request())
    recovered = [r.recovered for r in records]
    for prev, curr in zip(recovered[:-1], recovered[1:]):
        assert curr >= prev - 1e-6


def test_peak_infected_before_simulation_end():
    records = run_simulation(_make_request())
    peak = max(records, key=lambda r: r.infected)
    assert peak.day < records[-1].day


def test_rt_at_t0_equals_r0_when_fully_susceptible():
    request = _make_request(population=100_000, initial_infected=10)
    records = run_simulation(request)
    expected_r0 = request.beta / request.gamma
    # At t=0 nearly all are susceptible, so Rt ≈ R0.
    assert abs(records[0].rt - expected_r0) < 1e-3


def test_records_length_matches_days_plus_one():
    request = _make_request(days=50)
    records = run_simulation(request)
    assert len(records) == request.days + 1


def test_record_day_indices_are_monotonic_integers():
    request = _make_request(days=30)
    records = run_simulation(request)
    for i, r in enumerate(records):
        assert r.day == i


def test_compute_summary_no_herd_immunity_when_r0_low():
    request = _make_request(beta=0.05, gamma=0.10)
    records = run_simulation(request)
    summary = compute_summary(records, request.beta, request.gamma, request.population)
    assert summary.herd_immunity_reached is False


def test_compute_summary_herd_immunity_for_default_params():
    request = _make_request()
    records = run_simulation(request)
    summary = compute_summary(records, request.beta, request.gamma, request.population)
    assert summary.herd_immunity_reached is True


def test_compute_summary_outbreak_duration_zero_for_subcritical():
    # R0 = 0.05 / 0.10 = 0.5 with initial_infected=1: no outbreak; duration is 0.
    request = _make_request(beta=0.05, gamma=0.10, initial_infected=1)
    records = run_simulation(request)
    summary = compute_summary(records, request.beta, request.gamma, request.population)
    assert summary.outbreak_duration_days == 0


def test_compute_summary_peak_day_matches_argmax():
    request = _make_request()
    records = run_simulation(request)
    summary = compute_summary(records, request.beta, request.gamma, request.population)
    infected_array = np.array([r.infected for r in records])
    assert summary.peak_day == int(np.argmax(infected_array))


def test_initial_recovered_seeds_first_record():
    request = _make_request(initial_infected=10, initial_recovered=20_000)
    records = run_simulation(request)
    # Day 0 must reflect the seeded vaccinated/recovered fraction.
    assert records[0].recovered == pytest.approx(20_000, abs=1.0)
    assert records[0].susceptible == pytest.approx(
        request.population - 10 - 20_000, abs=1.0
    )


def test_initial_infected_plus_recovered_must_be_less_than_population():
    with pytest.raises(ValueError, match="strictly less than population"):
        SimulationRequest(
            population=1000,
            beta=0.3,
            gamma=0.1,
            initial_infected=500,
            initial_recovered=500,
            days=30,
            export_csv=False,
        )
