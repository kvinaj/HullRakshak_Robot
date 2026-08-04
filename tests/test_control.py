import unittest

from hullrakshak.applications.motion_test import (
    build_argument_parser,
    motion_limits_for_test,
    validate_physical_test_mode,
)
from hullrakshak.calibration import ClassifiedLineSensors, Surface
from hullrakshak.control.assisted import (
    DecisionKind,
    apply_obstacle_guard,
    line_following_decision,
)
from hullrakshak.control.motion import MotionDirection, MotionLimits
from hullrakshak.settings import load_settings
from hullrakshak.control.state import RobotMode, RobotStateMachine


class MotionLimitTests(unittest.TestCase):
    def test_rejects_excessive_speed_and_duration(self) -> None:
        limits = MotionLimits(maximum_speed=80, maximum_duration_ms=500)
        limits.validate(80, 500)
        with self.assertRaises(ValueError):
            limits.validate(81, 500)
        with self.assertRaises(ValueError):
            limits.validate(80, 501)

    def test_project_configuration_uses_conservative_limits(self) -> None:
        settings = load_settings()
        self.assertEqual(settings.safety.maximum_initial_speed, 100)
        self.assertEqual(settings.safety.maximum_command_duration_ms, 500)
        self.assertEqual(settings.safety.maximum_floor_test_duration_ms, 1500)
        self.assertEqual(settings.safety.teleop_pulse_duration_ms, 250)

    def test_one_shot_defaults_match_verified_raised_track_pulse(self) -> None:
        args = build_argument_parser().parse_args(["--direction", "forward"])
        self.assertEqual(args.speed, 100)
        self.assertEqual(args.duration_ms, 500)
        self.assertFalse(args.floor_test)

    def test_initial_floor_mode_permits_forward_only(self) -> None:
        validate_physical_test_mode(direction="forward", floor_test=True)
        with self.assertRaisesRegex(ValueError, "permits forward only"):
            validate_physical_test_mode(direction="left", floor_test=True)
        validate_physical_test_mode(direction="left", floor_test=False)

    def test_floor_mode_has_a_separate_duration_ceiling(self) -> None:
        settings = load_settings()
        raised_limits = motion_limits_for_test(settings, floor_test=False)
        floor_limits = motion_limits_for_test(settings, floor_test=True)
        self.assertEqual(raised_limits.maximum_duration_ms, 500)
        self.assertEqual(floor_limits.maximum_duration_ms, 1500)
        with self.assertRaises(ValueError):
            raised_limits.validate(100, 1500)
        floor_limits.validate(100, 1500)


class StateMachineTests(unittest.TestCase):
    def test_requires_safe_between_operating_modes(self) -> None:
        state = RobotStateMachine()
        state.transition(RobotMode.MANUAL)
        with self.assertRaises(ValueError):
            state.transition(RobotMode.AUTONOMOUS)
        state.transition(RobotMode.SAFE)
        state.transition(RobotMode.AUTONOMOUS)
        self.assertTrue(state.movement_allowed)

    def test_fault_disallows_movement_until_return_to_safe(self) -> None:
        state = RobotStateMachine(RobotMode.MANUAL)
        state.fault("connection lost")
        self.assertEqual(state.mode, RobotMode.FAULT)
        self.assertFalse(state.movement_allowed)
        state.transition(RobotMode.SAFE)
        self.assertIsNone(state.fault_reason)


class AssistedDecisionTests(unittest.TestCase):
    def test_obstacle_guard_stops_only_forward_motion(self) -> None:
        forward = apply_obstacle_guard(MotionDirection.FORWARD, 10, 15)
        reverse = apply_obstacle_guard(MotionDirection.BACKWARD, 10, 15)
        self.assertEqual(forward.kind, DecisionKind.STOP)
        self.assertEqual(reverse.kind, DecisionKind.MOVE)

    def test_centered_line_requests_forward_motion(self) -> None:
        decision = line_following_decision(
            ClassifiedLineSensors(
                left=Surface.LIGHT,
                middle=Surface.DARK,
                right=Surface.LIGHT,
            )
        )
        self.assertEqual(decision.kind, DecisionKind.MOVE)
        self.assertEqual(decision.direction, MotionDirection.FORWARD)

    def test_all_dark_stops_conservatively(self) -> None:
        decision = line_following_decision(
            ClassifiedLineSensors(
                left=Surface.DARK,
                middle=Surface.DARK,
                right=Surface.DARK,
            )
        )
        self.assertEqual(decision.kind, DecisionKind.STOP)


if __name__ == "__main__":
    unittest.main()
