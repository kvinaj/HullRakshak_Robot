"""Explicitly armed, pulse-based keyboard teleoperation."""

from __future__ import annotations

import argparse
import curses
import sys
import time
from pathlib import Path

from hullrakshak.applications.common import (
    add_connection_arguments,
    apply_connection_overrides,
    connect_robot,
)
from hullrakshak.control.motion import MotionDirection
from hullrakshak.control.state import RobotMode, RobotStateMachine
from hullrakshak.settings import DEFAULT_CONFIG_PATH, load_settings
from hullrakshak.transport.base import RobotConnectionError


KEY_DIRECTIONS = {
    ord("w"): MotionDirection.FORWARD,
    ord("s"): MotionDirection.BACKWARD,
    ord("a"): MotionDirection.LEFT,
    ord("d"): MotionDirection.RIGHT,
    curses.KEY_UP: MotionDirection.FORWARD,
    curses.KEY_DOWN: MotionDirection.BACKWARD,
    curses.KEY_LEFT: MotionDirection.LEFT,
    curses.KEY_RIGHT: MotionDirection.RIGHT,
}


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Low-speed, self-expiring keyboard control."
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_CONFIG_PATH,
        help="Path to robot.toml",
    )
    add_connection_arguments(parser)
    parser.add_argument(
        "--arm",
        action="store_true",
        help="Acknowledge that hardware movement is intended",
    )
    parser.add_argument(
        "--speed",
        type=int,
        help="PWM speed, bounded by the configured safety limit",
    )
    return parser


def require_physical_safety_confirmation(
    *, keyboard_controls_available: bool = True
) -> None:
    if not sys.stdin.isatty():
        raise SystemExit("Motion control requires an interactive terminal")
    print("SAFETY CHECK")
    print("- Both tracks must be raised clear of the bench.")
    print("- Keep the physical power switch within reach.")
    if keyboard_controls_available:
        print("- Space and Q command an immediate stop.")
    else:
        print("- The program will send stop after the single pulse.")
    confirmation = input("Type RAISED to arm motion: ").strip()
    if confirmation != "RAISED":
        raise SystemExit("Not armed; no movement command was sent.")


def run_terminal(
    screen: curses.window,
    *,
    robot: object,
    speed: int,
    pulse_duration_ms: int,
) -> None:
    # The object is a Robot at runtime. Keeping the annotation generic makes this
    # loop easy to substitute in future UI testing.
    drive_timed = getattr(robot, "drive_timed")
    stop = getattr(robot, "stop")

    screen.nodelay(True)
    screen.keypad(True)
    curses.curs_set(0)
    state = RobotStateMachine()
    state.transition(RobotMode.MANUAL)
    last_command_time = 0.0
    status = "armed and stopped"

    try:
        while True:
            screen.erase()
            screen.addstr(0, 0, "HullRakshak safe teleoperation")
            screen.addstr(2, 0, "W/A/S/D or arrows: timed movement pulse")
            screen.addstr(3, 0, "Space: STOP    Q: STOP and quit")
            screen.addstr(
                5,
                0,
                f"speed={speed}  pulse={pulse_duration_ms} ms  mode={state.mode.value}",
            )
            screen.addstr(7, 0, f"status: {status}")
            screen.refresh()

            key = screen.getch()
            now = time.monotonic()
            if key in (ord("q"), ord("Q")):
                stop()
                status = "stopped"
                break
            if key == ord(" "):
                stop()
                status = "emergency stop sent"
            elif key in KEY_DIRECTIONS and now - last_command_time >= 0.08:
                direction = KEY_DIRECTIONS[key]
                drive_timed(
                    direction,
                    speed=speed,
                    duration_ms=pulse_duration_ms,
                )
                last_command_time = now
                status = f"{direction.name.lower()} pulse sent"

            time.sleep(0.02)
    except Exception as error:
        state.fault(str(error))
        stop()
        raise
    finally:
        stop()
        if state.mode != RobotMode.FAULT:
            state.transition(RobotMode.SAFE)


def main() -> None:
    args = build_argument_parser().parse_args()
    if not args.arm:
        raise SystemExit(
            "Teleoperation is disarmed. Review docs/safety.md, raise the tracks, "
            "then explicitly supply --arm."
        )

    settings = apply_connection_overrides(load_settings(args.config), args)
    speed = (
        args.speed
        if args.speed is not None
        else settings.safety.maximum_initial_speed
    )
    # Validate before opening the serial connection or asking for confirmation.
    if not 1 <= speed <= settings.safety.maximum_initial_speed:
        raise SystemExit(
            f"Speed must be 1..{settings.safety.maximum_initial_speed}; "
            f"received {speed}."
        )

    require_physical_safety_confirmation()
    robot = connect_robot(settings, args.transport)
    try:
        with robot:
            curses.wrapper(
                run_terminal,
                robot=robot,
                speed=speed,
                pulse_duration_ms=settings.safety.teleop_pulse_duration_ms,
            )
    except KeyboardInterrupt:
        print("\nStopped safely.")
    except RobotConnectionError as error:
        raise SystemExit(f"Robot connection error: {error}") from error
