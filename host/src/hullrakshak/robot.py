"""High-level, transport-independent robot interface."""

from __future__ import annotations

import time
from typing import Protocol

from hullrakshak.protocol import encode_command, parse_labeled_integer
from hullrakshak.sensors.line import LineSensorReadings
from hullrakshak.settings import Settings
from hullrakshak.telemetry import TelemetrySnapshot
from hullrakshak.transport.serial import SerialTransport


class Transport(Protocol):
    def open(self) -> None: ...
    def close(self) -> None: ...
    def write(self, data: bytes) -> None: ...
    def read_frame(self, timeout_seconds: float) -> str: ...


class Robot:
    """Safe high-level API for the Conqueror robot."""

    LINE_SENSORS = (("L", 0), ("M", 1), ("R", 2))

    def __init__(self, transport: Transport, response_timeout_seconds: float) -> None:
        self.transport = transport
        self.response_timeout_seconds = response_timeout_seconds

    @classmethod
    def connect_serial(cls, settings: Settings) -> "Robot":
        return cls(
            SerialTransport(settings.serial),
            response_timeout_seconds=settings.serial.response_timeout_seconds,
        )

    def open(self) -> None:
        self.transport.open()
        self.stop()

    def close(self) -> None:
        try:
            self.stop()
        finally:
            self.transport.close()

    def __enter__(self) -> "Robot":
        self.open()
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def stop(self) -> None:
        """Enter standby. The factory protocol may return ``ok`` or no response."""
        self.transport.write(encode_command(100))

    def _query_integer(
        self,
        command_number: int,
        *,
        request_id: str,
        parameters: dict[str, int | str],
    ) -> int:
        self.transport.write(
            encode_command(
                command_number,
                request_id=request_id,
                parameters=parameters,
            )
        )

        deadline = time.monotonic() + self.response_timeout_seconds
        while time.monotonic() < deadline:
            remaining = max(0.01, deadline - time.monotonic())
            try:
                frame = self.transport.read_frame(remaining)
            except TimeoutError as error:
                raise TimeoutError(
                    f"No response for request {request_id} (command N={command_number}) "
                    f"within {self.response_timeout_seconds:.1f}s"
                ) from error
            value = parse_labeled_integer(frame, request_id)
            if value is not None:
                return value

        raise TimeoutError(
            f"No response for request {request_id} (command N={command_number}) "
            f"within {self.response_timeout_seconds:.1f}s"
        )

    def read_line_sensors(self) -> LineSensorReadings:
        values = {
            label: self._query_integer(
                22,
                request_id=label,
                parameters={"D1": sensor_index},
            )
            for label, sensor_index in self.LINE_SENSORS
        }
        return LineSensorReadings(
            left=values["L"],
            middle=values["M"],
            right=values["R"],
        )

    def read_ultrasonic_cm(self) -> int:
        return self._query_integer(21, request_id="U", parameters={"D1": 2})

    def read_telemetry(self) -> TelemetrySnapshot:
        return TelemetrySnapshot.now(
            line=self.read_line_sensors(),
            ultrasonic_cm=self.read_ultrasonic_cm(),
        )
