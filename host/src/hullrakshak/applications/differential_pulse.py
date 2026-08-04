"""Explicitly armed, capability-gated differential raised-track pulse."""

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
from hullrakshak.applications.teleop import require_physical_safety_confirmation
from hullrakshak.control.motion import DifferentialTimedMotion, MotionLimits
from hullrakshak.robot import Robot, UnsupportedFirmwareError
from hullrakshak.settings import DEFAULT_CONFIG_PATH, load_settings
from hullrakshak.transport.base import RobotConnectionError


class DifferentialRobot(Protocol):
    def __enter__(self) -> "DifferentialRobot": ...
    def __exit__(self, *args: object) -> None: ...
    def probe_differential_capability(self) -> bool: ...
    def drive_differential_timed(
        self, *, left_pwm: int, right_pwm: int, duration_ms: int
    ) -> None: ...
    def stop(self) -> None: ...


def run_differential_pulse(
    robot: DifferentialRobot,
    *,
    left_pwm: int,
    right_pwm: int,
    duration_ms: int,
    sleep: Callable[[float], None] = time.sleep,
) -> None:
    with robot:
        if not robot.probe_differential_capability():
            raise UnsupportedFirmwareError(
                "Differential pulse refused: connected firmware did not return CAP_1"
            )
        robot.drive_differential_timed(
            left_pwm=left_pwm,
            right_pwm=right_pwm,
            duration_ms=duration_ms,
        )
        sleep(duration_ms / 1000 + 0.25)
        robot.stop()


def validate_differential_test_mode(
    *, left_pwm: int, right_pwm: int, floor_test: bool
) -> None:
    if floor_test and not (
        (left_pwm > 0 and right_pwm > 0) or (left_pwm < 0 and right_pwm < 0)
    ):
        raise ValueError(
            "Differential floor-test mode requires nonzero PWM with the same "
            "sign on both tracks"
        )


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Send one capability-gated differential motion pulse."
    )
    parser.add_argument(
        "--config", type=Path, default=DEFAULT_CONFIG_PATH, help="Path to robot.toml"
    )
    add_connection_arguments(parser)
    parser.add_argument("--left-pwm", type=int, required=True)
    parser.add_argument("--right-pwm", type=int, required=True)
    parser.add_argument("--duration-ms", type=int, default=500)
    parser.add_argument(
        "--floor-test",
        action="store_true",
        help="Arm straight differential floor calibration",
    )
    parser.add_argument(
        "--arm",
        action="store_true",
        help="Acknowledge intentional differential motion",
    )
    return parser


def main() -> None:
    args = build_argument_parser().parse_args()
    if not args.arm:
        preparation = "Clear the floor path" if args.floor_test else "Raise both tracks"
        raise SystemExit(
            f"Differential pulse is disarmed. {preparation} and supply --arm."
        )

    settings = apply_connection_overrides(load_settings(args.config), args)
    try:
        validate_differential_test_mode(
            left_pwm=args.left_pwm,
            right_pwm=args.right_pwm,
            floor_test=args.floor_test,
        )
    except ValueError as error:
        raise SystemExit(f"Unsafe differential test rejected: {error}") from error

    limits = MotionLimits(
        maximum_speed=settings.safety.maximum_initial_speed,
        maximum_duration_ms=(
            settings.safety.maximum_differential_floor_test_duration_ms
            if args.floor_test
            else settings.safety.maximum_command_duration_ms
        ),
    )
    motion = DifferentialTimedMotion(
        left_pwm=args.left_pwm,
        right_pwm=args.right_pwm,
        duration_ms=args.duration_ms,
    )
    try:
        motion.validate(limits)
    except ValueError as error:
        raise SystemExit(f"Unsafe differential request rejected: {error}") from error

    require_physical_safety_confirmation(
        keyboard_controls_available=False,
        floor_test=args.floor_test,
        direction="backward" if args.left_pwm < 0 else "forward",
        tethered=args.transport == "serial",
    )
    robot: Robot = connect_robot(settings, args.transport, motion_limits=limits)
    try:
        print(
            "Sending one differential pulse: "
            f"left={args.left_pwm}, right={args.right_pwm}, "
            f"duration={args.duration_ms} ms"
        )
        run_differential_pulse(
            robot,
            left_pwm=args.left_pwm,
            right_pwm=args.right_pwm,
            duration_ms=args.duration_ms,
        )
        print("Pulse expired; stop sent. Test complete.")
    except KeyboardInterrupt:
        print("\nInterrupted; stop sent safely.")
    except (RobotConnectionError, UnsupportedFirmwareError) as error:
        raise SystemExit(str(error)) from error


if __name__ == "__main__":
    main()
