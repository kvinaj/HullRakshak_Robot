"""Interactive, labelled line-sensor calibration."""

from __future__ import annotations

import argparse
import time
from pathlib import Path

from hullrakshak.applications.common import (
    add_connection_arguments,
    apply_connection_overrides,
    connect_robot,
)
from hullrakshak.calibration import (
    DEFAULT_CALIBRATION_PATH,
    derive_line_calibration,
    save_line_calibration,
)
from hullrakshak.sensors.line import LineSensorReadings
from hullrakshak.settings import DEFAULT_CONFIG_PATH, load_settings
from hullrakshak.transport.base import RobotConnectionError


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Collect labelled light/dark samples and derive thresholds."
    )
    parser.add_argument(
        "--config", type=Path, default=DEFAULT_CONFIG_PATH, help="Path to robot.toml"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_CALIBRATION_PATH,
        help="Calibration TOML destination",
    )
    parser.add_argument(
        "--samples",
        type=int,
        default=20,
        help="Samples per surface (default: %(default)s)",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Allow replacing an existing calibration file",
    )
    add_connection_arguments(parser)
    return parser


def collect_samples(
    robot: object, surface_name: str, sample_count: int
) -> list[LineSensorReadings]:
    input(
        f"Place the {surface_name.upper()} reference beneath all three sensors, "
        "hold it steady, then press Enter."
    )
    read_line_sensors = getattr(robot, "read_line_sensors")
    samples: list[LineSensorReadings] = []
    for sample_number in range(1, sample_count + 1):
        reading = read_line_sensors()
        samples.append(reading)
        print(
            f"\r{surface_name} {sample_number:2d}/{sample_count}: "
            f"L={reading.left:4d} M={reading.middle:4d} R={reading.right:4d}",
            end="",
            flush=True,
        )
        time.sleep(0.1)
    print()
    return samples


def main() -> None:
    args = build_argument_parser().parse_args()
    if args.samples < 5:
        raise SystemExit("Use at least 5 samples per surface")
    if args.output.exists() and not args.overwrite:
        raise SystemExit(
            f"{args.output} already exists. Supply --overwrite only when you intend "
            "to replace the current calibration."
        )

    settings = apply_connection_overrides(load_settings(args.config), args)
    robot = connect_robot(settings, args.transport)
    try:
        with robot:
            print("Connected in read-only calibration mode.")
            light_samples = collect_samples(robot, "light", args.samples)
            dark_samples = collect_samples(robot, "dark", args.samples)
    except (RobotConnectionError, TimeoutError) as error:
        raise SystemExit(f"Robot connection error: {error}") from error

    calibration = derive_line_calibration(light_samples, dark_samples)
    save_line_calibration(
        calibration,
        args.output,
        source=f"interactive calibration, {args.samples} samples per surface",
    )
    print(f"Saved calibration to {args.output.resolve()}")
    for name in ("left", "middle", "right"):
        sensor = getattr(calibration, name)
        polarity = "above" if sensor.dark_values_are_higher else "below"
        print(
            f"{name:6s}: light={sensor.light_center:4d}, "
            f"dark={sensor.dark_center:4d}, threshold={sensor.threshold:4d}, "
            f"dark is {polarity} threshold"
        )
