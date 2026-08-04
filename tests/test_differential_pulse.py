import unittest

from hullrakshak.applications.differential_pulse import (
    run_differential_pulse,
    validate_differential_test_mode,
)
from hullrakshak.robot import UnsupportedFirmwareError


class FakeDifferentialRobot:
    def __init__(self, *, capable: bool = True) -> None:
        self.capable = capable
        self.events: list[object] = []

    def __enter__(self) -> "FakeDifferentialRobot":
        self.events.append("open_and_stop")
        return self

    def __exit__(self, *args: object) -> None:
        self.events.append("final_stop_and_close")

    def probe_differential_capability(self) -> bool:
        self.events.append("probe")
        return self.capable

    def drive_differential_timed(
        self, *, left_pwm: int, right_pwm: int, duration_ms: int
    ) -> None:
        self.events.append(("drive", left_pwm, right_pwm, duration_ms))

    def stop(self) -> None:
        self.events.append("stop")


class DifferentialPulseTests(unittest.TestCase):
    def test_floor_mode_requires_both_tracks_in_one_straight_direction(self) -> None:
        validate_differential_test_mode(
            left_pwm=100,
            right_pwm=95,
            floor_test=True,
        )
        validate_differential_test_mode(
            left_pwm=-100,
            right_pwm=-87,
            floor_test=True,
        )
        with self.assertRaisesRegex(ValueError, "same sign"):
            validate_differential_test_mode(
                left_pwm=-100,
                right_pwm=87,
                floor_test=True,
            )
        with self.assertRaisesRegex(ValueError, "nonzero PWM"):
            validate_differential_test_mode(
                left_pwm=100,
                right_pwm=0,
                floor_test=True,
            )
        validate_differential_test_mode(
            left_pwm=-100,
            right_pwm=-95,
            floor_test=False,
        )

    def test_verified_firmware_gets_one_bounded_pulse_and_stops(self) -> None:
        robot = FakeDifferentialRobot()
        delays: list[float] = []

        run_differential_pulse(
            robot,
            left_pwm=100,
            right_pwm=95,
            duration_ms=500,
            sleep=delays.append,
        )

        self.assertEqual(delays, [0.75])
        self.assertEqual(
            robot.events,
            [
                "open_and_stop",
                "probe",
                ("drive", 100, 95, 500),
                "stop",
                "final_stop_and_close",
            ],
        )

    def test_unverified_firmware_never_receives_motion(self) -> None:
        robot = FakeDifferentialRobot(capable=False)

        with self.assertRaises(UnsupportedFirmwareError):
            run_differential_pulse(
                robot,
                left_pwm=100,
                right_pwm=95,
                duration_ms=500,
                sleep=lambda seconds: None,
            )

        self.assertEqual(
            robot.events,
            ["open_and_stop", "probe", "final_stop_and_close"],
        )

    def test_exception_after_motion_still_closes_with_stop(self) -> None:
        robot = FakeDifferentialRobot()

        def fail_sleep(seconds: float) -> None:
            raise RuntimeError("observation failed")

        with self.assertRaisesRegex(RuntimeError, "observation failed"):
            run_differential_pulse(
                robot,
                left_pwm=100,
                right_pwm=95,
                duration_ms=500,
                sleep=fail_sleep,
            )

        self.assertEqual(robot.events[-1], "final_stop_and_close")


if __name__ == "__main__":
    unittest.main()
