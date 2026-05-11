"""Shared pytest fixtures for the epidemic simulator test suite."""

from unittest.mock import AsyncMock, MagicMock

import httpx
import matplotlib.pyplot as plt
import pytest
from fastapi.testclient import TestClient

from app.constants import (
    DEFAULT_BETA,
    DEFAULT_EXPORT_CSV,
    DEFAULT_GAMMA,
    DEFAULT_INITIAL_INFECTED,
    DEFAULT_POPULATION,
    DEFAULT_TIME_DAYS,
)
from app.main import app


@pytest.fixture(scope="module")
def client():
    """One TestClient instance per test module."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def default_simulation_request() -> dict:
    """Valid SimulationRequest payload using all default constants."""
    return {
        "population": DEFAULT_POPULATION,
        "beta": DEFAULT_BETA,
        "gamma": DEFAULT_GAMMA,
        "initial_infected": DEFAULT_INITIAL_INFECTED,
        "days": DEFAULT_TIME_DAYS,
        "export_csv": DEFAULT_EXPORT_CSV,
    }


@pytest.fixture
def default_spread_request() -> dict:
    """Valid SpreadRequest payload pointing at Tokyo."""
    return {
        "origin_lat": 35.68,
        "origin_lng": 139.69,
        "day": 30,
        "beta": 0.3,
        "gamma": 0.1,
    }


@pytest.fixture
def mock_news_api_failure(monkeypatch):
    """Force `httpx.AsyncClient.get` to raise so the news service falls back."""
    mock_client_instance = MagicMock()
    mock_client_instance.get = AsyncMock(side_effect=httpx.ConnectError("simulated"))

    mock_async_client = MagicMock()
    mock_async_client.return_value.__aenter__ = AsyncMock(
        return_value=mock_client_instance
    )
    mock_async_client.return_value.__aexit__ = AsyncMock(return_value=None)

    monkeypatch.setattr(
        "app.services.news_service.httpx.AsyncClient", mock_async_client
    )
    # Ensure the key is set so the fetch path runs (otherwise the service
    # short-circuits to fallback before the patched client is touched).
    monkeypatch.setenv("NEWS_API_KEY", "test-key")
    return mock_async_client


@pytest.fixture
def no_news_api_key(monkeypatch):
    """Ensure NEWS_API_KEY is absent so the fallback path runs."""
    monkeypatch.delenv("NEWS_API_KEY", raising=False)


@pytest.fixture(autouse=True, scope="function")
def close_matplotlib_figures():
    """Close all matplotlib figures after each test to prevent leak across tests."""
    yield
    plt.close("all")
