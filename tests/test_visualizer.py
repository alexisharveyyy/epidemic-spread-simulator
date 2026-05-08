"""Unit tests for the chart visualizer service."""

import base64

from app.models.response_models import DailyRecord
from app.services.visualizer import generate_sir_chart


def _synthetic_records(n: int = 30) -> list[DailyRecord]:
    records = []
    for day in range(n):
        s = max(0.0, 1000 - day * 30)
        i = max(0.0, min(500, day * 20))
        r = max(0.0, day * 10)
        records.append(
            DailyRecord(day=day, susceptible=s, infected=i, recovered=r, rt=1.5)
        )
    return records


def test_generate_sir_chart_returns_non_empty_string():
    chart = generate_sir_chart(
        _synthetic_records(), population=1000, beta=0.3, gamma=0.1
    )
    assert isinstance(chart, str)
    assert len(chart) > 0


def test_generate_sir_chart_returns_valid_base64():
    chart = generate_sir_chart(
        _synthetic_records(), population=1000, beta=0.3, gamma=0.1
    )
    # Will raise binascii.Error on invalid base64.
    decoded = base64.b64decode(chart)
    assert decoded


def test_generate_sir_chart_starts_with_png_magic_bytes():
    chart = generate_sir_chart(
        _synthetic_records(), population=1000, beta=0.3, gamma=0.1
    )
    decoded = base64.b64decode(chart)
    assert decoded.startswith(b"\x89PNG")


def test_generate_sir_chart_with_low_r0_is_valid():
    # R0 = 0.5, herd immunity threshold line should be omitted, no error raised.
    chart = generate_sir_chart(
        _synthetic_records(), population=1000, beta=0.05, gamma=0.10
    )
    decoded = base64.b64decode(chart)
    assert decoded.startswith(b"\x89PNG")
