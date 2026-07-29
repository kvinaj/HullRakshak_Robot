"""Timestamped robot telemetry."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from hullrakshak.sensors.line import LineSensorReadings


@dataclass(frozen=True)
class TelemetrySnapshot:
    timestamp: datetime
    line: LineSensorReadings
    ultrasonic_cm: int

    @classmethod
    def now(
        cls, line: LineSensorReadings, ultrasonic_cm: int
    ) -> "TelemetrySnapshot":
        return cls(
            timestamp=datetime.now(timezone.utc),
            line=line,
            ultrasonic_cm=ultrasonic_cm,
        )
