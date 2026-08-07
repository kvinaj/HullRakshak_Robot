import unittest
from datetime import datetime, timezone

from hullrakshak.applications.obstacle_guard import (
    classify_guard,
    run_guard_monitor,
)
from hullrakshak.sensors.line import LineSensorReadings
from hullrakshak.telemetry import TelemetrySnapshot


class FakeTelemetryRobot:
    def __init__(self, distance_cm: int) -> None:
        self.distance_cm = distance_cm
        self.opened = False

    def __enter__(self) -> "FakeTelemetryRobot":
        self.opened = True
        return self

    def __exit__(self, *args: object) -> None:
        self.opened = False

    def read_telemetry(self) -> TelemetrySnapshot:
        return TelemetrySnapshot(
            timestamp=datetime(2026, 8, 7, tzinfo=timezone.utc),
            line=LineSensorReadings(left=51, middle=54, right=47),
            ultrasonic_cm=self.distance_cm,
        )


class ObstacleGuardTests(unittest.TestCase):
    def test_threshold_and_below_stop(self) -> None:
        self.assertEqual(classify_guard(15, 15)[0], "STOP")
        self.assertEqual(classify_guard(9, 15)[0], "STOP")

    def test_above_threshold_is_clear(self) -> None:
        self.assertEqual(classify_guard(19, 15)[0], "CLEAR")

    def test_invalid_echo_stops_fail_safe(self) -> None:
        self.assertEqual(classify_guard(0, 15)[0], "STOP")

    def test_once_reads_one_snapshot_and_exits(self) -> None:
        robot = FakeTelemetryRobot(9)
        lines: list[str] = []
        run_guard_monitor(
            robot,
            stop_distance_cm=15,
            interval_seconds=0.5,
            once=True,
            output=lines.append,
            sleep=lambda _: self.fail("once mode must not sleep"),
        )
        self.assertFalse(robot.opened)
        self.assertEqual(len(lines), 1)
        self.assertIn("ultrasonic=  9 cm", lines[0])
        self.assertIn("guard=STOP", lines[0])


if __name__ == "__main__":
    unittest.main()
