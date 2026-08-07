"""Read-only ultrasonic obstacle-guard diagnostic."""

from __future__ import annotations

import argparse
import time
from collections.abc import Callable
from pathlib import Path
from typing import Protocol

from hullrakshak.applications.common import (
    add_connection_arguments,
    apply_connection_overrides,
    connect_robot,
)
from hullrakshak.control.assisted import DecisionKind, apply_obstacle_guard
from hullrakshak.control.motion import MotionDirection
from hullrakshak.settings import DEFAULT_CONFIG_PATH, load_settings
from hullrakshak.telemetry import TelemetrySnapshot
from hullrakshak.transport.base import RobotConnectionError


class TelemetryRobot(Protocol):
    def __enter__(self) -> "TelemetryRobot": ...
    def __exit__(self, *args: object) -> None: ...
    def read_telemetry(self) -> TelemetrySnapshot: ...


def classify_guard(ultrasonic_cm: int, stop_distance_cm: int) -> tuple[str, str]:
    """Return a fail-safe stationary guard label and explanation."""
    if ultrasonic_cm <= 0:
        return "STOP", "invalid or missing ultrasonic echo"
    decision = apply_obstacle_guard(
        MotionDirection.FORWARD,
        ultrasonic_cm,
        stop_distance_cm,
    )
    if decision.kind == DecisionKind.STOP:
        return "STOP", decision.reason
    return "CLEAR", decision.reason


def run_guard_monitor(
    robot: TelemetryRobot,
    *,
    stop_distance_cm: int,
    interval_seconds: float,
    once: bool,
    output: Callable[[str], None] = print,
    sleep: Callable[[float], None] = time.sleep,
) -> None:
    """Display decisions without ever issuing a movement command."""
    with robot:
        while True:
            snapshot = robot.read_telemetry()
            status, reason = classify_guard(
                snapshot.ultrasonic_cm,
                stop_distance_cm,
            )
            timestamp = snapshot.timestamp.astimezone().strftime("%H:%M:%S.%f")[:-3]
            output(
                f"{timestamp}  ultrasonic={snapshot.ultrasonic_cm:3d} cm  "
                f"guard={status}  threshold={stop_distance_cm} cm  ({reason})"
            )
            if once:
                return
            sleep(interval_seconds)


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Display read-only CLEAR/STOP ultrasonic decisions without moving "
            "the robot."
        )
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_CONFIG_PATH,
        help="Path to robot.toml",
    )
    add_connection_arguments(parser)
    parser.add_argument("--interval", type=float, help="Seconds between readings")
    parser.add_argument("--once", action="store_true", help="Read once and exit")
    return parser


def main() -> None:
    args = build_argument_parser().parse_args()
    settings = apply_connection_overrides(load_settings(args.config), args)
    interval = (
        args.interval
        if args.interval is not None
        else settings.monitor.interval_seconds
    )
    if interval <= 0:
        raise SystemExit("Interval must be greater than zero.")

    robot = connect_robot(settings, args.transport)
    threshold = settings.safety.obstacle_stop_distance_cm
    print("Opening read-only obstacle guard (motors will be commanded to stop)...")
    try:
        print(f"Configured STOP threshold: {threshold} cm; press Ctrl+C to stop.")
        run_guard_monitor(
            robot,
            stop_distance_cm=threshold,
            interval_seconds=interval,
            once=args.once,
        )
    except KeyboardInterrupt:
        print("\nStopped safely.")
    except (RobotConnectionError, TimeoutError) as error:
        raise SystemExit(f"Robot connection error: {error}") from error


if __name__ == "__main__":
    main()
