"""Validated motion commands for the factory TB6612 protocol."""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum


class MotionDirection(IntEnum):
    LEFT = 1
    RIGHT = 2
    FORWARD = 3
    BACKWARD = 4


@dataclass(frozen=True)
class MotionLimits:
    maximum_speed: int
    maximum_duration_ms: int

    def __post_init__(self) -> None:
        if not 1 <= self.maximum_speed <= 255:
            raise ValueError("maximum_speed must be within 1..255")
        if not 1 <= self.maximum_duration_ms <= 20_000:
            raise ValueError("maximum_duration_ms must be within 1..20000")

    def validate(self, speed: int, duration_ms: int) -> None:
        if not 1 <= speed <= self.maximum_speed:
            raise ValueError(
                f"speed must be within 1..{self.maximum_speed}; received {speed}"
            )
        if not 1 <= duration_ms <= self.maximum_duration_ms:
            raise ValueError(
                f"duration_ms must be within 1..{self.maximum_duration_ms}; "
                f"received {duration_ms}"
            )


@dataclass(frozen=True)
class TimedMotion:
    direction: MotionDirection
    speed: int
    duration_ms: int

    def validate(self, limits: MotionLimits) -> None:
        limits.validate(self.speed, self.duration_ms)
