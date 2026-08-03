"""Shared transport contracts and errors."""

from typing import Protocol


class RobotConnectionError(RuntimeError):
    """Raised when a robot connection cannot be established or is lost."""


class Transport(Protocol):
    def open(self) -> None: ...
    def close(self) -> None: ...
    def write(self, data: bytes) -> None: ...
    def read_frame(self, timeout_seconds: float) -> str: ...
