"""CSV export for SIR simulation records."""

import csv
import datetime
import logging
import pathlib

from app.models.response_models import DailyRecord

logger = logging.getLogger(__name__)

CSV_FIELDNAMES = ["day", "susceptible", "infected", "recovered", "rt"]


def build_csv_filename() -> str:
    """Return a filename of the form `simulation_YYYYMMDD_HHMMSS.csv` (UTC).

    The exact format is asserted in `tests/test_routes.py` and
    `tests/test_exporter.py` via:
        re.fullmatch(r"simulation_\\d{8}_\\d{6}\\.csv", path.name)
    """
    timestamp = datetime.datetime.now(tz=datetime.UTC).strftime("%Y%m%d_%H%M%S")
    return f"simulation_{timestamp}.csv"


def export_to_csv(
    records: list[DailyRecord],
    output_path: pathlib.Path,
) -> None:
    """Write `DailyRecord`s to disk as a CSV with all five columns.

    Creates parent directories as needed so the call is safe on first run
    when the `data/` directory may not yet exist on a fresh checkout.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=CSV_FIELDNAMES)
        writer.writeheader()
        for record in records:
            writer.writerow(
                {
                    "day": record.day,
                    "susceptible": record.susceptible,
                    "infected": record.infected,
                    "recovered": record.recovered,
                    "rt": record.rt,
                }
            )
