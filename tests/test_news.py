"""Tests for the Outbreak Intelligence Feed."""

from datetime import datetime, timedelta, timezone

from app.services.news_service import format_relative_time, tag_severity


def test_news_endpoint_returns_fallback_without_key(client, no_news_api_key):
    response = client.get("/api/news")
    assert response.status_code == 200
    body = response.json()
    assert isinstance(body, list)
    assert len(body) > 0


def test_fallback_articles_have_required_fields(client, no_news_api_key):
    response = client.get("/api/news")
    body = response.json()
    for article in body:
        assert article["headline"]
        assert article["source"]
        assert article["severity"] in {"critical", "moderate", "watch"}
        assert article["time"]


def test_tag_severity_critical():
    assert tag_severity("Outbreak declared in coastal region") == "critical"


def test_tag_severity_moderate():
    assert tag_severity("Surge in cases reported") == "moderate"


def test_tag_severity_watch():
    assert tag_severity("Routine surveillance update") == "watch"


def test_news_refresh_endpoint(client, no_news_api_key):
    response = client.get("/api/news/refresh")
    assert response.status_code == 200
    body = response.json()
    assert isinstance(body, list)
    assert len(body) > 0


def test_news_endpoint_cache_header(client, no_news_api_key):
    response = client.get("/api/news")
    assert response.headers.get("cache-control") == "max-age=60"


def test_news_refresh_endpoint_cache_header(client, no_news_api_key):
    response = client.get("/api/news/refresh")
    assert response.headers.get("cache-control") == "no-cache"


def test_news_falls_back_when_upstream_fails(client, mock_news_api_failure):
    response = client.get("/api/news")
    assert response.status_code == 200
    body = response.json()
    assert isinstance(body, list)
    assert len(body) > 0


def _iso(delta: timedelta) -> str:
    return (datetime.now(timezone.utc) - delta).isoformat()


def test_format_relative_time_minutes():
    assert format_relative_time(_iso(timedelta(minutes=5))) == "5m ago"


def test_format_relative_time_hours():
    assert format_relative_time(_iso(timedelta(hours=2))) == "2h ago"


def test_format_relative_time_days():
    assert format_relative_time(_iso(timedelta(days=3))) == "3d ago"


def test_format_relative_time_future_returns_just_now():
    future = (datetime.now(timezone.utc) + timedelta(seconds=30)).isoformat()
    assert format_relative_time(future) == "just now"
