"""Measured line-sensor calibration and surface classification."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from datetime import date
from enum import Enum
from pathlib import Path
from statistics import median

from hullrakshak.sensors.line import LineSensorReadings
from hullrakshak.settings import PROJECT_ROOT


DEFAULT_CALIBRATION_PATH = PROJECT_ROOT / "config" / "calibration.toml"


class Surface(str, Enum):
    LIGHT = "light"
    DARK = "dark"


@dataclass(frozen=True)
class SensorCalibration:
    light_center: int
    dark_center: int
    threshold: int
    dark_values_are_higher: bool

    def classify(self, value: int) -> Surface:
        is_dark = (
            value >= self.threshold
            if self.dark_values_are_higher
            else value <= self.threshold
        )
        return Surface.DARK if is_dark else Surface.LIGHT


@dataclass(frozen=True)
class ClassifiedLineSensors:
    left: Surface
    middle: Surface
    right: Surface


@dataclass(frozen=True)
class LineCalibration:
    left: SensorCalibration
    middle: SensorCalibration
    right: SensorCalibration

    def classify(self, readings: LineSensorReadings) -> ClassifiedLineSensors:
        return ClassifiedLineSensors(
            left=self.left.classify(readings.left),
            middle=self.middle.classify(readings.middle),
            right=self.right.classify(readings.right),
        )


def derive_line_calibration(
    light_samples: list[LineSensorReadings],
    dark_samples: list[LineSensorReadings],
    *,
    minimum_separation: int = 100,
) -> LineCalibration:
    """Derive robust per-sensor thresholds from labelled sample sets."""
    if not light_samples or not dark_samples:
        raise ValueError("Both light and dark samples are required")

    def derive(name: str) -> SensorCalibration:
        light_center = round(median(getattr(sample, name) for sample in light_samples))
        dark_center = round(median(getattr(sample, name) for sample in dark_samples))
        if abs(dark_center - light_center) < minimum_separation:
            raise ValueError(
                f"{name} sensor separation is too small: "
                f"light={light_center}, dark={dark_center}"
            )
        return SensorCalibration(
            light_center=light_center,
            dark_center=dark_center,
            threshold=round((light_center + dark_center) / 2),
            dark_values_are_higher=dark_center > light_center,
        )

    calibration = LineCalibration(
        left=derive("left"),
        middle=derive("middle"),
        right=derive("right"),
    )
    polarities = {
        calibration.left.dark_values_are_higher,
        calibration.middle.dark_values_are_higher,
        calibration.right.dark_values_are_higher,
    }
    if len(polarities) != 1:
        raise ValueError("Line sensors reported inconsistent light/dark polarity")
    return calibration


def save_line_calibration(
    calibration: LineCalibration,
    path: Path,
    *,
    source: str,
) -> None:
    """Write calibration using the project's dependency-free TOML schema."""
    path.parent.mkdir(parents=True, exist_ok=True)
    dark_values_are_higher = calibration.left.dark_values_are_higher
    lines = [
        "[metadata]",
        f'source = "{source}"',
        f'recorded_at = "{date.today().isoformat()}"',
        f"dark_values_are_higher = {str(dark_values_are_higher).lower()}",
        "",
    ]
    for name in ("left", "middle", "right"):
        sensor = getattr(calibration, name)
        lines.extend(
            [
                f"[line.{name}]",
                f"light_center = {sensor.light_center}",
                f"dark_center = {sensor.dark_center}",
                f"threshold = {sensor.threshold}",
                "",
            ]
        )
    path.write_text("\n".join(lines), encoding="utf-8")


def load_line_calibration(
    path: Path = DEFAULT_CALIBRATION_PATH,
) -> LineCalibration:
    with path.open("rb") as calibration_file:
        raw = tomllib.load(calibration_file)

    dark_values_are_higher = bool(raw["metadata"]["dark_values_are_higher"])

    def sensor(name: str) -> SensorCalibration:
        values = raw["line"][name]
        return SensorCalibration(
            light_center=int(values["light_center"]),
            dark_center=int(values["dark_center"]),
            threshold=int(values["threshold"]),
            dark_values_are_higher=dark_values_are_higher,
        )

    return LineCalibration(
        left=sensor("left"),
        middle=sensor("middle"),
        right=sensor("right"),
    )
