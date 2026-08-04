"""High-level, transport-independent robot interface."""

from __future__ import annotations

import time

from hullrakshak.control.motion import (
    DifferentialTimedMotion,
    MotionDirection,
    MotionLimits,
    TimedMotion,
)
from hullrakshak.protocol import encode_command, parse_labeled_integer
from hullrakshak.sensors.line import LineSensorReadings
from hullrakshak.settings import Settings
from hullrakshak.telemetry import TelemetrySnapshot
from hullrakshak.transport.base import Transport
from hullrakshak.transport.serial import SerialTransport
from hullrakshak.transport.simulated import SimulatedTransport
from hullrakshak.transport.wifi import WifiTransport


class UnsupportedFirmwareError(RuntimeError):
    """Raised before a command unsupported by the connected UNO is written."""


class Robot:
    """Safe high-level API for the Conqueror robot."""

    LINE_SENSORS = (("L", 0), ("M", 1), ("R", 2))

    def __init__(
        self,
        transport: Transport,
        response_timeout_seconds: float,
        motion_limits: MotionLimits,
    ) -> None:
        self.transport = transport
        self.response_timeout_seconds = response_timeout_seconds
        self.motion_limits = motion_limits
        self._differential_capability_verified = False

    @classmethod
    def connect_serial(
        cls, settings: Settings, motion_limits: MotionLimits | None = None
    ) -> "Robot":
        return cls(
            SerialTransport(settings.serial),
            response_timeout_seconds=settings.serial.response_timeout_seconds,
            motion_limits=motion_limits or MotionLimits(
                maximum_speed=settings.safety.maximum_initial_speed,
                maximum_duration_ms=settings.safety.maximum_command_duration_ms,
            ),
        )

    @classmethod
    def connect_wifi(
        cls, settings: Settings, motion_limits: MotionLimits | None = None
    ) -> "Robot":
        return cls(
            WifiTransport(settings.wifi),
            response_timeout_seconds=settings.wifi.response_timeout_seconds,
            motion_limits=motion_limits or MotionLimits(
                maximum_speed=settings.safety.maximum_initial_speed,
                maximum_duration_ms=settings.safety.maximum_command_duration_ms,
            ),
        )

    @classmethod
    def connect_simulated(
        cls, settings: Settings, motion_limits: MotionLimits | None = None
    ) -> "Robot":
        return cls(
            SimulatedTransport(),
            response_timeout_seconds=0.1,
            motion_limits=motion_limits or MotionLimits(
                maximum_speed=settings.safety.maximum_initial_speed,
                maximum_duration_ms=settings.safety.maximum_command_duration_ms,
            ),
        )

    def open(self) -> None:
        self._differential_capability_verified = False
        self.transport.open()
        try:
            self.stop()
        except BaseException:
            self.transport.close()
            raise

    def close(self) -> None:
        try:
            self.stop()
        finally:
            self._differential_capability_verified = False
            self.transport.close()

    def __enter__(self) -> "Robot":
        self.open()
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def stop(self) -> None:
        """Enter standby. The factory protocol may return ``ok`` or no response."""
        self.transport.write(encode_command(100))

    def drive_timed(
        self,
        direction: MotionDirection,
        *,
        speed: int,
        duration_ms: int,
    ) -> None:
        """Send one validated, self-expiring factory motion command."""
        motion = TimedMotion(direction, speed, duration_ms)
        motion.validate(self.motion_limits)
        self.transport.write(
            encode_command(
                2,
                request_id="MOVE",
                parameters={
                    "D1": int(direction),
                    "D2": speed,
                    "T": duration_ms,
                },
            )
        )

    def probe_differential_capability(self) -> bool:
        """Verify the custom UNO handshake without sending a motion command."""
        self._differential_capability_verified = False
        self.transport.write(encode_command(41, request_id="CAP"))
        deadline = time.monotonic() + self.response_timeout_seconds
        while time.monotonic() < deadline:
            remaining = max(0.01, deadline - time.monotonic())
            try:
                frame = self.transport.read_frame(remaining)
            except TimeoutError:
                return False
            if frame == "CAP_1":
                self._differential_capability_verified = True
                return True
        return False

    def drive_differential_timed(
        self,
        *,
        left_pwm: int,
        right_pwm: int,
        duration_ms: int,
    ) -> None:
        """Send N=40 only after the current connection passed the N=41 probe."""
        motion = DifferentialTimedMotion(left_pwm, right_pwm, duration_ms)
        motion.validate(self.motion_limits)
        if not self._differential_capability_verified:
            raise UnsupportedFirmwareError(
                "Differential motion refused: N=41 capability was not verified "
                "on the current connection"
            )
        self.transport.write(
            encode_command(
                40,
                request_id="DMOVE",
                parameters={
                    "L": left_pwm,
                    "R": right_pwm,
                    "T": duration_ms,
                },
            )
        )

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
