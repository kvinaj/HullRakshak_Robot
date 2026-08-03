"""Pure decision logic for future assisted and autonomous control."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from hullrakshak.calibration import ClassifiedLineSensors, Surface
from hullrakshak.control.motion import MotionDirection


class DecisionKind(str, Enum):
    MOVE = "move"
    STOP = "stop"
    SEARCH = "search"


@dataclass(frozen=True)
class MotionDecision:
    kind: DecisionKind
    direction: MotionDirection | None
    reason: str


def apply_obstacle_guard(
    requested_direction: MotionDirection,
    ultrasonic_cm: int,
    stop_distance_cm: int,
) -> MotionDecision:
    """Stop forward motion at close range; allow retreat and turning."""
    if (
        requested_direction == MotionDirection.FORWARD
        and 0 < ultrasonic_cm <= stop_distance_cm
    ):
        return MotionDecision(
            DecisionKind.STOP,
            None,
            f"obstacle at {ultrasonic_cm} cm",
        )
    return MotionDecision(DecisionKind.MOVE, requested_direction, "path permitted")


def line_following_decision(
    surfaces: ClassifiedLineSensors,
) -> MotionDecision:
    """Return a conservative direction from the three calibrated sensors."""
    dark = Surface.DARK
    if surfaces.middle == dark and surfaces.left != dark and surfaces.right != dark:
        return MotionDecision(
            DecisionKind.MOVE, MotionDirection.FORWARD, "line centered"
        )
    if surfaces.left == dark and surfaces.right != dark:
        return MotionDecision(
            DecisionKind.MOVE, MotionDirection.LEFT, "line detected on left"
        )
    if surfaces.right == dark and surfaces.left != dark:
        return MotionDecision(
            DecisionKind.MOVE, MotionDirection.RIGHT, "line detected on right"
        )
    if (
        surfaces.left == dark
        and surfaces.middle == dark
        and surfaces.right == dark
    ):
        return MotionDecision(DecisionKind.STOP, None, "all sensors detect dark")
    return MotionDecision(DecisionKind.SEARCH, None, "line not detected")
