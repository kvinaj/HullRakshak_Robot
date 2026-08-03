"""Continuously display read-only robot telemetry."""

from __future__ import annotations

import argparse
import time
from contextlib import nullcontext
from pathlib import Path

from hullrakshak.calibration import (
    DEFAULT_CALIBRATION_PATH,
    load_line_calibration,
)
from hullrakshak.applications.common import (
    add_connection_arguments,
    apply_connection_overrides,
    connect_robot,
)
from hullrakshak.data_logging import CsvTelemetryWriter
from hullrakshak.settings import DEFAULT_CONFIG_PATH, load_settings
from hullrakshak.transport.base import RobotConnectionError


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Read line and ultrasonic sensors without moving the robot."
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_CONFIG_PATH,
        help="Path to robot.toml",
    )
    add_connection_arguments(parser)
    parser.add_argument("--interval", type=float, help="Seconds between readings")
    parser.add_argument(
        "--once", action="store_true", help="Read one telemetry snapshot and exit"
    )
    parser.add_argument(
        "--log",
        type=Path,
        metavar="CSV_PATH",
        help="Append every telemetry snapshot to this CSV file",
    )
    parser.add_argument(
        "--classify",
        action="store_true",
        help="Display calibrated light/dark classification for each line sensor",
    )
    parser.add_argument(
        "--calibration",
        type=Path,
        default=DEFAULT_CALIBRATION_PATH,
        help="Path to line-sensor calibration TOML",
    )
    return parser


def main() -> None:
    args = build_argument_parser().parse_args()
    settings = load_settings(args.config)
    settings = apply_connection_overrides(settings, args)
    interval = (
        args.interval
        if args.interval is not None
        else settings.monitor.interval_seconds
    )
    calibration = load_line_calibration(args.calibration) if args.classify else None

    try:
        robot = connect_robot(settings, args.transport)
        print("Opening robot connection (motors will be commanded to stop)...")
        logger_context = (
            CsvTelemetryWriter(args.log) if args.log else nullcontext(None)
        )
        with robot, logger_context as logger:
            print("Connected. Read-only telemetry; press Ctrl+C to stop.")
            if args.log:
                print(f"Logging telemetry to {args.log.resolve()}")
            while True:
                snapshot = robot.read_telemetry()
                if logger is not None:
                    logger.write(snapshot)
                timestamp = snapshot.timestamp.astimezone().strftime("%H:%M:%S.%f")[:-3]
                line = snapshot.line
                print(
                    f"{timestamp}  "
                    f"line[L={line.left:4d} M={line.middle:4d} R={line.right:4d}]  "
                    f"ultrasonic={snapshot.ultrasonic_cm:3d} cm",
                    end="",
                )
                if calibration is not None:
                    classified = calibration.classify(line)
                    print(
                        "  surface["
                        f"L={classified.left.value} "
                        f"M={classified.middle.value} "
                        f"R={classified.right.value}]"
                    )
                else:
                    print()
                if args.once:
                    break
                time.sleep(interval)
    except KeyboardInterrupt:
        print("\nStopped safely.")
    except (RobotConnectionError, TimeoutError) as error:
        raise SystemExit(f"Robot connection error: {error}") from error
