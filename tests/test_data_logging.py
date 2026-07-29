import csv
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from hullrakshak.data_logging import CsvTelemetryWriter
from hullrakshak.sensors.line import LineSensorReadings
from hullrakshak.telemetry import TelemetrySnapshot


class CsvTelemetryWriterTests(unittest.TestCase):
    def test_writes_stable_header_and_snapshot(self) -> None:
        snapshot = TelemetrySnapshot(
            timestamp=datetime(2026, 7, 29, 20, 0, tzinfo=timezone.utc),
            line=LineSensorReadings(left=181, middle=193, right=73),
            ultrasonic_cm=42,
        )

        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "telemetry.csv"
            with CsvTelemetryWriter(path) as writer:
                writer.write(snapshot)

            with path.open(newline="", encoding="utf-8") as csv_file:
                rows = list(csv.DictReader(csv_file))

        self.assertEqual(
            rows,
            [
                {
                    "timestamp_utc": "2026-07-29T20:00:00+00:00",
                    "line_left": "181",
                    "line_middle": "193",
                    "line_right": "73",
                    "ultrasonic_cm": "42",
                }
            ],
        )


if __name__ == "__main__":
    unittest.main()
