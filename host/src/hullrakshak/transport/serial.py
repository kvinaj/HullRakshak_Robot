"""USB serial transport for the UNO controller."""

from __future__ import annotations

import time
from collections import deque

import serial
from serial.tools import list_ports

from hullrakshak.protocol import FrameDecoder
from hullrakshak.settings import SerialSettings
from hullrakshak.transport.base import RobotConnectionError


def discover_serial_port() -> str:
    """Find the most likely macOS serial device for the robot UNO."""
    ports = list(list_ports.comports())
    preferred: list[str] = []
    fallback: list[str] = []

    for port in ports:
        device = port.device
        description = f"{port.description} {port.manufacturer or ''}".lower()
        if not device.startswith("/dev/cu."):
            continue
        if any(
            marker in description
            for marker in ("arduino", "ch340", "wch", "usb serial", "usb-serial")
        ) or any(marker in device.lower() for marker in ("usbserial", "wchusbserial")):
            preferred.append(device)
        else:
            fallback.append(device)

    candidates = preferred or fallback
    if not candidates:
        available = ", ".join(port.device for port in ports) or "none"
        raise RobotConnectionError(
            "No suitable serial port found. Available ports: " + available
        )
    if len(candidates) > 1:
        raise RobotConnectionError(
            "Multiple possible serial ports found; select one with --port: "
            + ", ".join(candidates)
        )
    return candidates[0]


class SerialTransport:
    """Read and write framed protocol messages over USB."""

    def __init__(self, settings: SerialSettings) -> None:
        self.settings = settings
        self.port = settings.port or discover_serial_port()
        self._connection: serial.Serial | None = None
        self._decoder = FrameDecoder()
        self._frames: deque[str] = deque()

    @property
    def is_open(self) -> bool:
        return self._connection is not None and self._connection.is_open

    def open(self) -> None:
        if self.is_open:
            return
        try:
            self._connection = serial.Serial(
                self.port,
                self.settings.baudrate,
                timeout=0.1,
                write_timeout=1.0,
            )
        except serial.SerialException as error:
            raise RobotConnectionError(
                f"Could not open {self.port}. Close Arduino Serial Monitor and try "
                f"again. Original error: {error}"
            ) from error

        time.sleep(self.settings.reset_delay_seconds)
        self._connection.reset_input_buffer()

    def close(self) -> None:
        if self._connection is not None:
            self._connection.close()
            self._connection = None

    def write(self, data: bytes) -> None:
        if not self.is_open or self._connection is None:
            raise RobotConnectionError("Serial connection is not open")
        self._connection.write(data)
        self._connection.flush()

    def read_frame(self, timeout_seconds: float) -> str:
        if not self.is_open or self._connection is None:
            raise RobotConnectionError("Serial connection is not open")

        deadline = time.monotonic() + timeout_seconds
        while time.monotonic() < deadline:
            if self._frames:
                return self._frames.popleft()

            waiting = self._connection.in_waiting
            data = self._connection.read(waiting or 1)
            self._frames.extend(self._decoder.feed(data))

        raise TimeoutError(f"No complete robot response within {timeout_seconds:.1f}s")
