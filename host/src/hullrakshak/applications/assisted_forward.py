"""Explicitly armed, ultrasonic-guarded forward floor movement."""

from __future__ import annotations

import argparse
import sys
import time
from collections.abc import Callable
from pathlib import Path
from typing import Protocol

from hullrakshak.applications.common import (
    add_connection_arguments,
    apply_connection_overrides,
    connect_robot,
)
from hullrakshak.applications.obstacle_guard import classify_guard
from hullrakshak.settings import DEFAULT_CONFIG_PATH, load_settings
from hullrakshak.transport.base import RobotConnectionError


class AssistedRobot(Protocol):
    def __enter__(self) -> "AssistedRobot": ...
    def __exit__(self, *args: object) -> None: ...
    def probe_differential_capability(self) -> bool: ...
    def read_ultrasonic_cm(self) -> int: ...
    def drive_differential_timed(
        self, *, left_pwm: int, right_pwm: int, duration_ms: int
    ) -> None: ...
    def stop(self) -> None: ...


def select_pulse_duration_ms(
    distance_cm: int,
    *,
    medium_distance_cm: int,
    near_distance_cm: int,
    far_pulse_ms: int,
    medium_pulse_ms: int,
    near_pulse_ms: int,
) -> int:
    """Select progressively shorter pulses as the obstacle gets closer."""
    if distance_cm <= near_distance_cm:
        return near_pulse_ms
    if distance_cm <= medium_distance_cm:
        return medium_pulse_ms
    return far_pulse_ms


def run_assisted_forward(
    robot: AssistedRobot,
    *,
    left_pwm: int,
    right_pwm: int,
    pulse_duration_ms: int,
    medium_distance_cm: int,
    medium_pulse_duration_ms: int,
    near_distance_cm: int,
    near_pulse_duration_ms: int,
    stop_distance_cm: int,
    maximum_run_seconds: float,
    output: Callable[[str], None] = print,
    sleep: Callable[[float], None] = time.sleep,
    monotonic: Callable[[], float] = time.monotonic,
) -> str:
    """Move in bounded pulses until obstacle, invalid echo, or time limit."""
    with robot:
        if not robot.probe_differential_capability():
            raise RuntimeError(
                "Assisted motion refused: differential firmware capability "
                "was not verified."
            )
        started_at = monotonic()
        while True:
            distance_cm = robot.read_ultrasonic_cm()
            guard, reason = classify_guard(distance_cm, stop_distance_cm)
            if guard == "STOP":
                output(f"ultrasonic={distance_cm} cm  guard={guard}  ({reason})")
                robot.stop()
                return "obstacle"
            if monotonic() - started_at >= maximum_run_seconds:
                robot.stop()
                output(f"Maximum runtime {maximum_run_seconds:.1f}s reached; STOP")
                return "timeout"
            selected_pulse_ms = select_pulse_duration_ms(
                distance_cm,
                medium_distance_cm=medium_distance_cm,
                near_distance_cm=near_distance_cm,
                far_pulse_ms=pulse_duration_ms,
                medium_pulse_ms=medium_pulse_duration_ms,
                near_pulse_ms=near_pulse_duration_ms,
            )
            output(
                f"ultrasonic={distance_cm} cm  guard={guard}  "
                f"pulse={selected_pulse_ms} ms  ({reason})"
            )
            robot.drive_differential_timed(
                left_pwm=left_pwm,
                right_pwm=right_pwm,
                duration_ms=selected_pulse_ms,
            )
            sleep(selected_pulse_ms / 1000)


def require_assisted_confirmation() -> None:
    if not sys.stdin.isatty():
        raise SystemExit("Assisted motion requires an interactive terminal.")
    print("ASSISTED-FORWARD SAFETY CHECK")
    print("- Use a flat floor with at least 2 m of controlled test space.")
    print("- Place a large, flat obstacle across the robot's forward path.")
    print("- Keep away from stairs, drop-offs, people, and pets.")
    print("- No USB cable may be attached to the moving robot.")
    print("- Keep the physical power switch within reach.")
    print("- Motion uses adaptive 250/150/75 ms self-expiring pulses.")
    print("- The complete assisted session stops after at most 60 seconds.")
    confirmation = input("Type GUARDED to arm assisted forward motion: ").strip()
    if confirmation != "GUARDED":
        raise SystemExit("Not armed; no movement command was sent.")


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Move forward in bounded pulses until the ultrasonic guard stops "
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
    parser.add_argument(
        "--floor-test",
        action="store_true",
        help="Acknowledge controlled untethered floor testing",
    )
    parser.add_argument("--arm", action="store_true")
    return parser


def main() -> None:
    args = build_argument_parser().parse_args()
    if args.transport != "wifi" or not args.floor_test:
        raise SystemExit(
            "Assisted forward requires --transport wifi and --floor-test."
        )
    if not args.arm:
        raise SystemExit("Assisted forward is disarmed; supply --arm.")

    settings = apply_connection_overrides(load_settings(args.config), args)
    if not settings.drive.forward_trim_enabled:
        raise SystemExit("Assisted forward requires calibrated forward trim.")
    require_assisted_confirmation()
    robot = connect_robot(settings, args.transport)
    try:
        result = run_assisted_forward(
            robot,
            left_pwm=settings.drive.forward_left_pwm,
            right_pwm=settings.drive.forward_right_pwm,
            pulse_duration_ms=settings.safety.assisted_pulse_duration_ms,
            medium_distance_cm=settings.safety.assisted_medium_distance_cm,
            medium_pulse_duration_ms=(
                settings.safety.assisted_medium_pulse_duration_ms
            ),
            near_distance_cm=settings.safety.assisted_near_distance_cm,
            near_pulse_duration_ms=settings.safety.assisted_near_pulse_duration_ms,
            stop_distance_cm=settings.safety.obstacle_stop_distance_cm,
            maximum_run_seconds=settings.safety.maximum_assisted_run_seconds,
        )
        print(f"Assisted-forward test complete: {result}; stop sent.")
    except KeyboardInterrupt:
        print("\nInterrupted; stop sent safely.")
    except (RobotConnectionError, TimeoutError, RuntimeError) as error:
        raise SystemExit(f"Assisted-forward error: {error}") from error


if __name__ == "__main__":
    main()
