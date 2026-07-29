"""Line-tracking sensor values."""

from dataclasses import dataclass


@dataclass(frozen=True)
class LineSensorReadings:
    left: int
    middle: int
    right: int

    def __post_init__(self) -> None:
        for name, value in (
            ("left", self.left),
            ("middle", self.middle),
            ("right", self.right),
        ):
            if not 0 <= value <= 1023:
                raise ValueError(f"{name} line-sensor value is outside 0..1023: {value}")
