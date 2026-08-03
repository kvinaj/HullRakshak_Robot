"""Deterministic in-process robot transport for development without hardware."""

from __future__ import annotations

import json
import queue
from dataclasses import dataclass

from hullrakshak.control.motion import MotionDirection, TimedMotion
from hullrakshak.transport.base import RobotConnectionError


@dataclass
class SimulatedSensors:
    line_left: int = 154
    line_middle: int = 180
    line_right: int = 84
    ultrasonic_cm: int = 42


class SimulatedTransport:
    """Implement the factory protocol locally and record motion requests."""

    def __init__(self, sensors: SimulatedSensors | None = None) -> None:
        self.sensors = sensors or SimulatedSensors()
        self.is_open = False
        self.motion_history: list[TimedMotion] = []
        self.stop_count = 0
        self._frames: queue.Queue[str] = queue.Queue()

    def open(self) -> None:
        self.is_open = True

    def close(self) -> None:
        self.is_open = False

    def write(self, data: bytes) -> None:
        if not self.is_open:
            raise RobotConnectionError("Simulated connection is not open")
        command = json.loads(data)
        command_number = int(command["N"])
        request_id = str(command.get("H", ""))

        if command_number == 100:
            self.stop_count += 1
        elif command_number == 22:
            values = {
                0: self.sensors.line_left,
                1: self.sensors.line_middle,
                2: self.sensors.line_right,
            }
            self._frames.put(f"{request_id}_{values[int(command['D1'])]}")
        elif command_number == 21 and int(command["D1"]) == 2:
            self._frames.put(f"{request_id}_{self.sensors.ultrasonic_cm}")
        elif command_number == 2:
            self.motion_history.append(
                TimedMotion(
                    direction=MotionDirection(int(command["D1"])),
                    speed=int(command["D2"]),
                    duration_ms=int(command["T"]),
                )
            )

    def read_frame(self, timeout_seconds: float) -> str:
        try:
            return self._frames.get(timeout=timeout_seconds)
        except queue.Empty as error:
            raise TimeoutError(
                f"No simulated response within {timeout_seconds:.1f}s"
            ) from error
