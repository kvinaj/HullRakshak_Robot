"""Explicitly armed raw serial diagnostic for the factory timed-motion command."""

from __future__ import annotations

import argparse
import time
from collections.abc import Callable
from dataclasses import replace
from datetime import datetime
from pathlib import Path
from typing import Protocol

import serial

from hullrakshak.applications.teleop import require_physical_safety_confirmation
from hullrakshak.control.motion import MotionDirection
from hullrakshak.protocol import encode_command
from hullrakshak.settings import DEFAULT_CONFIG_PATH, SerialSettings, load_settings
from hullrakshak.transport.serial import discover_serial_port


MOVEMENT_BYTES = encode_command(
    2,
    request_id="MOVE",
    parameters={
        "D1": int(MotionDirection.FORWARD),
        "D2": 80,
        "T": 500,
    },
)
STOP_BYTES = encode_command(100)
OBSERVATION_SECONDS = 3.0

assert MOVEMENT_BYTES == b'{"N":2,"D1":3,"D2":80,"T":500,"H":"MOVE"}'
assert STOP_BYTES == b'{"N":100}'


class RawSerialConnection(Protocol):
    is_open: bool
    in_waiting: int

    def write(self, data: bytes) -> int | None: ...

    def flush(self) -> None: ...

    def read(self, size: int = 1) -> bytes: ...

    def reset_input_buffer(self) -> None: ...

    def close(self) -> None: ...


EventWriter = Callable[[str, bytes], None]


class BraceFrameCapture:
    """Capture complete brace-delimited frames while preserving exact bytes."""

    def __init__(self) -> None:
        self._frame: bytearray | None = None

    def feed(self, data: bytes) -> list[bytes]:
        frames: list[bytes] = []
        for byte in data:
            if byte == ord("{"):
                self._frame = bytearray((byte,))
            elif self._frame is not None:
                self._frame.append(byte)
                if byte == ord("}"):
                    frames.append(bytes(self._frame))
                    self._frame = None
        return frames


def print_event(kind: str, data: bytes) -> None:
    timestamp = datetime.now().astimezone().isoformat(timespec="milliseconds")
    print(f"{timestamp}  {kind:<5}  {data!r}", flush=True)


def transmit(
    connection: RawSerialConnection,
    data: bytes,
    *,
    event_writer: EventWriter = print_event,
) -> None:
    connection.write(data)
    connection.flush()
    event_writer("TX", data)


def observe_raw_serial(
    connection: RawSerialConnection,
    *,
    duration_seconds: float = OBSERVATION_SECONDS,
    event_writer: EventWriter = print_event,
    monotonic: Callable[[], float] = time.monotonic,
) -> None:
    frames = BraceFrameCapture()
    deadline = monotonic() + duration_seconds
    while monotonic() < deadline:
        received = connection.read(connection.in_waiting or 1)
        if not received:
            continue
        event_writer("RX", received)
        for frame in frames.feed(received):
            event_writer("FRAME", frame)


def run_diagnostic(
    settings: SerialSettings,
    *,
    serial_factory: Callable[..., RawSerialConnection] = serial.Serial,
    sleep: Callable[[float], None] = time.sleep,
    observer: Callable[..., None] = observe_raw_serial,
    event_writer: EventWriter = print_event,
) -> None:
    port = settings.port or discover_serial_port()
    connection: RawSerialConnection | None = None
    try:
        connection = serial_factory(
            port,
            settings.baudrate,
            timeout=0.1,
            write_timeout=1.0,
        )
        sleep(settings.reset_delay_seconds)
        connection.reset_input_buffer()

        transmit(connection, STOP_BYTES, event_writer=event_writer)
        transmit(connection, MOVEMENT_BYTES, event_writer=event_writer)
        observer(
            connection,
            duration_seconds=OBSERVATION_SECONDS,
            event_writer=event_writer,
        )
    finally:
        if connection is not None and connection.is_open:
            try:
                transmit(connection, STOP_BYTES, event_writer=event_writer)
            finally:
                connection.close()


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Raw serial diagnostic for the factory timed-motion command."
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_CONFIG_PATH,
        help="Path to robot.toml",
    )
    parser.add_argument("--port", help="Override serial port auto-discovery")
    parser.add_argument(
        "--arm",
        action="store_true",
        help="Acknowledge intentional raised-track motor testing",
    )
    return parser


def main() -> None:
    args = build_argument_parser().parse_args()
    if not args.arm:
        raise SystemExit(
            "Serial diagnostic is disarmed. Raise both tracks and explicitly "
            "supply --arm."
        )

    require_physical_safety_confirmation(keyboard_controls_available=False)
    settings = load_settings(args.config).serial
    if args.port:
        settings = replace(settings, port=args.port)

    try:
        run_diagnostic(settings)
    except KeyboardInterrupt:
        print("\nInterrupted; stop sent and serial port closed.")
    except serial.SerialException as error:
        raise SystemExit(f"Serial diagnostic error: {error}") from error
