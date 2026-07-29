"""Persistent telemetry logging."""

from __future__ import annotations

import csv
from pathlib import Path
from types import TracebackType
from typing import TextIO

from hullrakshak.telemetry import TelemetrySnapshot


class CsvTelemetryWriter:
    """Write telemetry snapshots to a stable, analysis-friendly CSV schema."""

    FIELDNAMES = (
        "timestamp_utc",
        "line_left",
        "line_middle",
        "line_right",
        "ultrasonic_cm",
    )

    def __init__(self, path: Path) -> None:
        self.path = path
        self._file: TextIO | None = None
        self._writer: csv.DictWriter[str] | None = None

    def open(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        file_is_empty = not self.path.exists() or self.path.stat().st_size == 0
        self._file = self.path.open("a", newline="", encoding="utf-8")
        self._writer = csv.DictWriter(self._file, fieldnames=self.FIELDNAMES)
        if file_is_empty:
            self._writer.writeheader()
            self._file.flush()

    def write(self, snapshot: TelemetrySnapshot) -> None:
        if self._file is None or self._writer is None:
            raise RuntimeError("CSV telemetry writer is not open")
        self._writer.writerow(
            {
                "timestamp_utc": snapshot.timestamp.isoformat(),
                "line_left": snapshot.line.left,
                "line_middle": snapshot.line.middle,
                "line_right": snapshot.line.right,
                "ultrasonic_cm": snapshot.ultrasonic_cm,
            }
        )
        # Preserve every completed sample if the process or connection fails.
        self._file.flush()

    def close(self) -> None:
        if self._file is not None:
            self._file.close()
            self._file = None
            self._writer = None

    def __enter__(self) -> "CsvTelemetryWriter":
        self.open()
        return self

    def __exit__(
        self,
        exception_type: type[BaseException] | None,
        exception: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.close()
