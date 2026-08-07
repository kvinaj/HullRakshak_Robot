import unittest

from hullrakshak.applications.assisted_forward import (
    run_assisted_forward,
    select_pulse_duration_ms,
)


class FakeAssistedRobot:
    def __init__(self, distances: list[int], *, capable: bool = True) -> None:
        self.distances = iter(distances)
        self.capable = capable
        self.events: list[object] = []

    def __enter__(self) -> "FakeAssistedRobot":
        self.events.append("open_and_stop")
        return self

    def __exit__(self, *args: object) -> None:
        self.events.append("final_stop_and_close")

    def probe_differential_capability(self) -> bool:
        self.events.append("probe")
        return self.capable

    def read_ultrasonic_cm(self) -> int:
        value = next(self.distances)
        self.events.append(("distance", value))
        return value

    def drive_differential_timed(
        self, *, left_pwm: int, right_pwm: int, duration_ms: int
    ) -> None:
        self.events.append(("drive", left_pwm, right_pwm, duration_ms))

    def stop(self) -> None:
        self.events.append("stop")


class AssistedForwardTests(unittest.TestCase):
    def run_test(self, robot: FakeAssistedRobot, **overrides: object) -> str:
        arguments = {
            "left_pwm": 100,
            "right_pwm": 86,
            "pulse_duration_ms": 250,
            "medium_distance_cm": 30,
            "medium_pulse_duration_ms": 150,
            "near_distance_cm": 20,
            "near_pulse_duration_ms": 75,
            "stop_distance_cm": 15,
            "maximum_run_seconds": 10.0,
            "output": lambda line: None,
            "sleep": lambda seconds: None,
            "monotonic": lambda: 0.0,
        }
        arguments.update(overrides)
        return run_assisted_forward(robot, **arguments)  # type: ignore[arg-type]

    def test_close_obstacle_prevents_all_motion(self) -> None:
        robot = FakeAssistedRobot([9])
        self.assertEqual(self.run_test(robot), "obstacle")
        self.assertNotIn(("drive", 100, 86, 250), robot.events)
        self.assertEqual(robot.events[-2:], ["stop", "final_stop_and_close"])

    def test_clear_path_pulses_then_stops_at_obstacle(self) -> None:
        robot = FakeAssistedRobot([40, 25, 18, 15])
        self.assertEqual(self.run_test(robot), "obstacle")
        self.assertIn(("drive", 100, 86, 250), robot.events)
        self.assertIn(("drive", 100, 86, 150), robot.events)
        self.assertIn(("drive", 100, 86, 75), robot.events)
        self.assertEqual(robot.events[-2:], ["stop", "final_stop_and_close"])

    def test_adaptive_pulse_boundaries(self) -> None:
        parameters = {
            "medium_distance_cm": 30,
            "near_distance_cm": 20,
            "far_pulse_ms": 250,
            "medium_pulse_ms": 150,
            "near_pulse_ms": 75,
        }
        self.assertEqual(select_pulse_duration_ms(31, **parameters), 250)
        self.assertEqual(select_pulse_duration_ms(30, **parameters), 150)
        self.assertEqual(select_pulse_duration_ms(21, **parameters), 150)
        self.assertEqual(select_pulse_duration_ms(20, **parameters), 75)
        self.assertEqual(select_pulse_duration_ms(16, **parameters), 75)

    def test_invalid_echo_prevents_motion(self) -> None:
        robot = FakeAssistedRobot([0])
        self.assertEqual(self.run_test(robot), "obstacle")
        self.assertFalse(any(event[0] == "drive" for event in robot.events if isinstance(event, tuple)))

    def test_timeout_stops_before_another_pulse(self) -> None:
        robot = FakeAssistedRobot([40])
        clock = iter([0.0, 10.0])
        self.assertEqual(
            self.run_test(robot, monotonic=lambda: next(clock)),
            "timeout",
        )
        self.assertNotIn(("drive", 100, 86, 250), robot.events)

    def test_missing_capability_prevents_sensor_and_motion_commands(self) -> None:
        robot = FakeAssistedRobot([40], capable=False)
        with self.assertRaisesRegex(RuntimeError, "capability"):
            self.run_test(robot)
        self.assertEqual(
            robot.events,
            ["open_and_stop", "probe", "final_stop_and_close"],
        )


if __name__ == "__main__":
    unittest.main()
