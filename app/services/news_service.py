"""Outbreak Intelligence Feed service.

Fetches live headlines from NewsAPI when `NEWS_API_KEY` is configured,
otherwise falls back to a curated synthetic feed. All HTTP errors,
parse errors, and non-OK NewsAPI responses degrade gracefully to the
fallback list - the caller never sees an exception.
"""

import logging
import os
from datetime import datetime, timedelta, timezone

import httpx

from app.constants import (
    NEWS_API_BASE_URL,
    NEWS_PAGE_SIZE,
    NEWS_QUERY,
    NEWS_TIMEOUT_CONNECT,
    NEWS_TIMEOUT_READ,
)
from app.models.response_models import NewsArticle

logger = logging.getLogger(__name__)


# Synthetic fallback used when NEWS_API_KEY is unset or the upstream call fails.
# Computed at module import time so timestamps look fresh on first request.
_NOW = datetime.now(timezone.utc)
FALLBACK_HEADLINES: list[dict] = [
    {
        "headline": "Health authorities monitor cluster of respiratory cases in coastal region",
        "source": "Public Health Wire",
        "published_at": (_NOW - timedelta(minutes=12)).isoformat(),
        "url": None,
    },
    {
        "headline": "Surge in vector-borne illness reported across three southern districts",
        "source": "Regional Health Bulletin",
        "published_at": (_NOW - timedelta(minutes=47)).isoformat(),
        "url": None,
    },
    {
        "headline": "Resistant strain detected in routine surveillance sampling",
        "source": "Surveillance Daily",
        "published_at": (_NOW - timedelta(minutes=95)).isoformat(),
        "url": None,
    },
    {
        "headline": "Veterinary outbreak declared at agricultural processing facility",
        "source": "AgriHealth Report",
        "published_at": (_NOW - timedelta(minutes=180)).isoformat(),
        "url": None,
    },
    {
        "headline": "Novel pathogen identified in environmental water samples",
        "source": "Environmental Sentinel",
        "published_at": (_NOW - timedelta(minutes=360)).isoformat(),
        "url": None,
    },
    {
        "headline": "Cross-border quarantine imposed following confirmed transmission",
        "source": "Global Health Tracker",
        "published_at": (_NOW - timedelta(minutes=720)).isoformat(),
        "url": None,
    },
]

# Ordered tier-to-keywords map. Iteration order matters: critical keywords are
# tested first so a headline that contains both a critical and a moderate term
# is tagged as critical.
SEVERITY_KEYWORD_MAP: dict[str, list[str]] = {
    "critical": [
        "outbreak declared",
        "novel pathogen",
        "hemorrhagic",
        "pandemic",
        "emergency declared",
        "quarantine imposed",
    ],
    "moderate": [
        "surge",
        "cluster",
        "rise",
        "resistant",
        "spread",
        "cases reported",
    ],
}


def tag_severity(headline: str) -> str:
    """Tag a headline with one of `critical`, `moderate`, or `watch`.

    Uses case-insensitive substring matching. Keyword matching can produce
    occasional false positives (e.g., `"rise"` matching inside `"sunrise"`);
    a word-boundary regex is listed as a TODO extension in the README.
    """
    lowered = headline.lower()
    for tier, keywords in SEVERITY_KEYWORD_MAP.items():
        if any(keyword in lowered for keyword in keywords):
            return tier
    return "watch"


def format_relative_time(published_at: str) -> str:
    """Format an ISO 8601 timestamp as a human-readable relative string.

    Returns:
        - "just now" for negative deltas (clock skew) or under 60s
        - "{m}m ago" under 1h
        - "{h}h ago" under 24h
        - "{d}d ago" otherwise

    Raises:
        ValueError: If `published_at` cannot be parsed as ISO 8601.
    """
    try:
        parsed = datetime.fromisoformat(published_at.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(
            f"Could not parse ISO 8601 timestamp: {published_at!r}"
        ) from exc

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)

    delta = datetime.now(timezone.utc) - parsed
    seconds = delta.total_seconds()

    # Future timestamp (clock skew between client and server) or under one minute.
    if seconds < 60:
        return "just now"
    if seconds < 3600:
        return f"{int(seconds // 60)}m ago"
    if seconds < 86400:
        return f"{int(seconds // 3600)}h ago"
    return f"{int(seconds // 86400)}d ago"


def _build_fallback_articles() -> list[NewsArticle]:
    """Convert FALLBACK_HEADLINES into NewsArticle objects.

    Severity and time are computed at request time (not module load time)
    so the fallback feed always reflects current rules and looks fresh.
    """
    return [
        NewsArticle(
            headline=item["headline"],
            source=item["source"],
            severity=tag_severity(item["headline"]),
            time=format_relative_time(item["published_at"]),
            url=item["url"],
        )
        for item in FALLBACK_HEADLINES
    ]


async def fetch_headlines() -> list[NewsArticle]:
    """Return the current outbreak headline feed.

    Reads `NEWS_API_KEY` from the environment at call time so tests can
    patch it via `monkeypatch`. When the key is missing or any error
    occurs, returns the synthetic fallback list. Never raises.
    """
    # Read at call time (not module import) so tests can patch it.
    api_key = os.environ.get("NEWS_API_KEY", "")
    if not api_key:
        return _build_fallback_articles()

    try:
        # `async with` is required to ensure the connection pool is properly
        # closed; without the context manager, sockets leak in long-running
        # server processes.
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(
                connect=NEWS_TIMEOUT_CONNECT,
                read=NEWS_TIMEOUT_READ,
                write=3.0,
                pool=3.0,
            ),
            limits=httpx.Limits(max_connections=5),
        ) as client:
            response = await client.get(
                NEWS_API_BASE_URL,
                params={
                    "q": NEWS_QUERY,
                    "language": "en",
                    "sortBy": "publishedAt",
                    "pageSize": NEWS_PAGE_SIZE,
                    "apiKey": api_key,
                },
            )
            response.raise_for_status()
            payload = response.json()

        if payload.get("status") != "ok":
            raise ValueError(
                f"NewsAPI returned non-ok status: {payload.get('status')!r}"
            )

        articles: list[NewsArticle] = []
        for item in payload.get("articles", []):
            title = item.get("title")
            if not title:
                continue
            articles.append(
                NewsArticle(
                    headline=title,
                    source=item.get("source", {}).get("name", "Unknown"),
                    severity=tag_severity(title),
                    time=format_relative_time(item["publishedAt"]),
                    url=item.get("url"),
                )
            )
        if not articles:
            # Empty upstream result is treated as a soft failure so the UI
            # always has something to render.
            return _build_fallback_articles()
    except Exception as exc:
        logger.warning("News fetch failed: %s", exc)
        return _build_fallback_articles()
    else:
        return articles
