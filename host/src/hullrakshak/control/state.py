"""Explicit operating-state transitions."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class RobotMode(str, Enum):
    SAFE = "safe"
    MANUAL = "manual"
    ASSISTED = "assisted"
    AUTONOMOUS = "autonomous"
    FAULT = "fault"


ALLOWED_TRANSITIONS: dict[RobotMode, frozenset[RobotMode]] = {
    RobotMode.SAFE: frozenset(
        {RobotMode.MANUAL, RobotMode.ASSISTED, RobotMode.AUTONOMOUS, RobotMode.FAULT}
    ),
    RobotMode.MANUAL: frozenset({RobotMode.SAFE, RobotMode.FAULT}),
    RobotMode.ASSISTED: frozenset({RobotMode.SAFE, RobotMode.FAULT}),
    RobotMode.AUTONOMOUS: frozenset({RobotMode.SAFE, RobotMode.FAULT}),
    RobotMode.FAULT: frozenset({RobotMode.SAFE}),
}


@dataclass
class RobotStateMachine:
    mode: RobotMode = RobotMode.SAFE
    fault_reason: str | None = None

    def transition(self, target: RobotMode) -> None:
        if target == self.mode:
            return
        if target not in ALLOWED_TRANSITIONS[self.mode]:
            raise ValueError(f"Invalid robot-mode transition: {self.mode} -> {target}")
        if self.mode == RobotMode.FAULT and target == RobotMode.SAFE:
            self.fault_reason = None
        self.mode = target

    def fault(self, reason: str) -> None:
        if not reason.strip():
            raise ValueError("A fault reason is required")
        self.fault_reason = reason
        self.mode = RobotMode.FAULT

    @property
    def movement_allowed(self) -> bool:
        return self.mode in {
            RobotMode.MANUAL,
            RobotMode.ASSISTED,
            RobotMode.AUTONOMOUS,
        }
