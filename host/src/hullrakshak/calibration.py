"""Measured line-sensor calibration and surface classification."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

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
