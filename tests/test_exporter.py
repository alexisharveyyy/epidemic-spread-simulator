"""Unit tests for the CSV exporter service."""

import csv
import re

from app.models.response_models import DailyRecord
from app.services.exporter import build_csv_filename, export_to_csv


def _synthetic_records(n: int = 5) -> list[DailyRecord]:
    return [
        DailyRecord(
            day=day,
            susceptible=1000.0 - day,
            infected=float(day),
            recovered=0.0,
            rt=1.5,
        )
        for day in range(n)
    ]


def test_build_csv_filename_format():
    name = build_csv_filename()
    assert re.fullmatch(r"simulation_\d{8}_\d{6}\.csv", name)


def test_export_to_csv_writes_expected_columns(tmp_path):
    out = tmp_path / "out.csv"
    export_to_csv(_synthetic_records(), out)

    with out.open("r", encoding="utf-8") as f:
        reader = csv.reader(f)
        headers = next(reader)
    assert headers == ["day", "susceptible", "infected", "recovered", "rt"]


def test_export_to_csv_creates_parent_directory(tmp_path):
    nested = tmp_path / "nested" / "data"
    out = nested / "out.csv"
    assert not nested.exists()
    export_to_csv(_synthetic_records(), out)
    assert out.exists()


def test_export_to_csv_row_count_matches_records(tmp_path):
    records = _synthetic_records(n=12)
    out = tmp_path / "out.csv"
    export_to_csv(records, out)
    with out.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    assert len(rows) == len(records)
