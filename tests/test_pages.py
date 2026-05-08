"""Integration tests for every server-rendered page."""

import pytest

PAGE_FIXTURES = [
    ("/",            "home",        ["EPIDEMIC SPREAD SIMULATOR"]),
    ("/about",       "about",       ["COMPARTMENTAL MODEL"]),
    ("/scenarios",   "scenarios",   ["SCENARIO LIBRARY"]),
    ("/history",     "history",     ["SIMULATION HISTORY"]),
    ("/sensitivity", "sensitivity", ["SENSITIVITY ANALYSIS"]),
    ("/vaccination", "vaccination", ["VACCINATION SCENARIOS"]),
    ("/glossary",    "glossary",    ["GLOSSARY"]),
    ("/author",      "author",      ["ABOUT THE BUILDER"]),
    ("/credits",     "credits",     ["CREDITS"]),
    ("/roadmap",     "roadmap",     ["ROADMAP"]),
]

SHARED_NAV_HREFS = ["/", "/scenarios", "/sensitivity", "/vaccination", "/history", "/about", "/glossary"]


@pytest.mark.parametrize("path,active_key,markers", PAGE_FIXTURES)
def test_page_renders(client, path, active_key, markers):
    response = client.get(path)
    assert response.status_code == 200, f"{path} returned {response.status_code}"
    assert response.headers["content-type"].startswith("text/html")
    body = response.text
    for marker in markers:
        assert marker.upper() in body.upper(), f"{path} missing marker {marker!r}"


@pytest.mark.parametrize("path,active_key,markers", PAGE_FIXTURES)
def test_page_has_active_nav_link(client, path, active_key, markers):
    response = client.get(path)
    body = response.text
    # The active nav link is rendered with `class="active"`. For author /
    # credits / roadmap the active link is in the footer; for everything else
    # it is in the top nav. Either way, `class="active"` must appear at least
    # once on the page.
    assert 'class="active"' in body, f"{path} has no active link"


@pytest.mark.parametrize("path,active_key,markers", PAGE_FIXTURES)
def test_page_has_shared_nav(client, path, active_key, markers):
    response = client.get(path)
    body = response.text
    for href in SHARED_NAV_HREFS:
        assert f'href="{href}"' in body, f"{path} is missing nav link to {href}"
