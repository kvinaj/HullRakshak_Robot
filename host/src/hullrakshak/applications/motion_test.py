"""One-shot raised-track or explicitly armed floor-motion validation."""

from __future__ import annotations

import argparse
import time
from pathlib import Path

from hullrakshak.applications.common import (
    add_connection_arguments,
    apply_connection_overrides,
    connect_robot,
)
from hullrakshak.applications.teleop import require_physical_safety_confirmation
from hullrakshak.control.motion import MotionDirection, MotionLimits
from hullrakshak.settings import DEFAULT_CONFIG_PATH, Settings, load_settings
from hullrakshak.transport.base import RobotConnectionError


DIRECTION_NAMES = {
    "left": MotionDirection.LEFT,
    "right": MotionDirection.RIGHT,
    "forward": MotionDirection.FORWARD,
    "backward": MotionDirection.BACKWARD,
}


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Send exactly one bounded, self-expiring movement pulse."
    )
    parser.add_argument(
        "--config", type=Path, default=DEFAULT_CONFIG_PATH, help="Path to robot.toml"
    )
    add_connection_arguments(parser)
    parser.add_argument(
        "--direction",
        choices=tuple(DIRECTION_NAMES),
        required=True,
        help="Pulse direction",
    )
    parser.add_argument("--speed", type=int, default=100, help="PWM speed")
    parser.add_argument(
        "--duration-ms",
        type=int,
        default=500,
        help="Pulse duration in milliseconds",
    )
    parser.add_argument(
        "--arm",
        action="store_true",
        help="Acknowledge that one hardware movement pulse is intended",
    )
    parser.add_argument(
        "--floor-test",
        action="store_true",
        help="Arm a controlled straight floor test instead of a raised-track test",
    )
    return parser


def validate_physical_test_mode(*, direction: str, floor_test: bool) -> None:
    """Keep floor commissioning narrower than raised-track testing."""
    if floor_test and direction not in ("forward", "backward"):
        raise ValueError("Floor-test mode permits forward and backward only")


def motion_limits_for_test(settings: Settings, *, floor_test: bool) -> MotionLimits:
    safety = settings.safety
    maximum_duration_ms = (
        safety.maximum_floor_test_duration_ms
        if floor_test
        else safety.maximum_command_duration_ms
    )
    return MotionLimits(
        maximum_speed=safety.maximum_initial_speed,
        maximum_duration_ms=maximum_duration_ms,
    )


def main() -> None:
    args = build_argument_parser().parse_args()
    if not args.arm:
        preparation = "Clear the floor path" if args.floor_test else "Raise both tracks"
        raise SystemExit(f"Motion test is disarmed. {preparation} and supply --arm.")

    try:
        validate_physical_test_mode(
            direction=args.direction,
            floor_test=args.floor_test,
        )
    except ValueError as error:
        raise SystemExit(f"Unsafe physical test rejected: {error}") from error

    settings = apply_connection_overrides(load_settings(args.config), args)
    limits = motion_limits_for_test(settings, floor_test=args.floor_test)
    try:
        limits.validate(args.speed, args.duration_ms)
    except ValueError as error:
        raise SystemExit(f"Unsafe motion request rejected: {error}") from error

    require_physical_safety_confirmation(
        keyboard_controls_available=False,
        floor_test=args.floor_test,
        direction=args.direction,
    )
    direction = DIRECTION_NAMES[args.direction]
    robot = connect_robot(settings, args.transport, motion_limits=limits)

    try:
        with robot:
            print(
                f"Sending one {args.direction} pulse: "
                f"speed={args.speed}, duration={args.duration_ms} ms"
            )
            robot.drive_timed(
                direction,
                speed=args.speed,
                duration_ms=args.duration_ms,
            )
            time.sleep(args.duration_ms / 1000 + 0.25)
            robot.stop()
            print("Pulse expired; stop sent. Test complete.")
    except RobotConnectionError as error:
        raise SystemExit(f"Robot connection error: {error}") from error
