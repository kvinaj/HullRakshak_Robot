import json
import unittest

from hullrakshak.control.motion import MotionDirection, MotionLimits
from hullrakshak.robot import Robot, UnsupportedFirmwareError
from hullrakshak.settings import load_settings
from hullrakshak.transport.simulated import SimulatedTransport


class FakeTransport:
    VALUES = {"L": 181, "M": 193, "R": 73, "U": 42}

    def __init__(self, *, differential_capability: bool = False) -> None:
        self.is_open = False
        self.differential_capability = differential_capability
        self.responses: list[str] = []
        self.commands: list[dict[str, object]] = []

    def open(self) -> None:
        self.is_open = True

    def close(self) -> None:
        self.is_open = False

    def write(self, data: bytes) -> None:
        command = json.loads(data)
        self.commands.append(command)
        request_id = command.get("H")
        if command.get("N") == 41 and self.differential_capability:
            self.responses.append("CAP_1")
        if request_id in self.VALUES:
            self.responses.append(f"{request_id}_{self.VALUES[request_id]}")

    def read_frame(self, timeout_seconds: float) -> str:
        if not self.responses:
            raise TimeoutError
        return self.responses.pop(0)


class RobotTests(unittest.TestCase):
    def test_read_telemetry_uses_sensor_protocol(self) -> None:
        transport = FakeTransport()
        robot = Robot(
            transport,
            response_timeout_seconds=0.1,
            motion_limits=MotionLimits(maximum_speed=80, maximum_duration_ms=500),
        )

        with robot:
            snapshot = robot.read_telemetry()

        self.assertEqual(snapshot.line.left, 181)
        self.assertEqual(snapshot.line.middle, 193)
        self.assertEqual(snapshot.line.right, 73)
        self.assertEqual(snapshot.ultrasonic_cm, 42)
        self.assertEqual(transport.commands[0], {"N": 100})
        self.assertEqual(transport.commands[-1], {"N": 100})

    def test_timed_motion_is_bounded_and_encoded(self) -> None:
        transport = FakeTransport()
        robot = Robot(
            transport,
            response_timeout_seconds=0.1,
            motion_limits=MotionLimits(maximum_speed=80, maximum_duration_ms=500),
        )

        with robot:
            robot.drive_timed(
                MotionDirection.FORWARD,
                speed=60,
                duration_ms=250,
            )

        self.assertIn(
            {"N": 2, "D1": 3, "D2": 60, "T": 250, "H": "MOVE"},
            transport.commands,
        )

    def test_timed_motion_rejects_unsafe_values_before_write(self) -> None:
        transport = FakeTransport()
        robot = Robot(
            transport,
            response_timeout_seconds=0.1,
            motion_limits=MotionLimits(maximum_speed=80, maximum_duration_ms=500),
        )
        transport.open()

        with self.assertRaises(ValueError):
            robot.drive_timed(
                MotionDirection.FORWARD,
                speed=81,
                duration_ms=250,
            )

        self.assertEqual(transport.commands, [])

    def test_factory_firmware_cannot_receive_differential_motion(self) -> None:
        transport = FakeTransport()
        robot = Robot(
            transport,
            response_timeout_seconds=0.01,
            motion_limits=MotionLimits(maximum_speed=100, maximum_duration_ms=500),
        )

        with robot:
            self.assertFalse(robot.probe_differential_capability())
            with self.assertRaises(UnsupportedFirmwareError):
                robot.drive_differential_timed(
                    left_pwm=95,
                    right_pwm=100,
                    duration_ms=500,
                )

        self.assertFalse(any(command["N"] == 40 for command in transport.commands))

    def test_verified_candidate_encodes_bounded_differential_motion(self) -> None:
        transport = FakeTransport(differential_capability=True)
        robot = Robot(
            transport,
            response_timeout_seconds=0.1,
            motion_limits=MotionLimits(maximum_speed=100, maximum_duration_ms=500),
        )

        with robot:
            self.assertTrue(robot.probe_differential_capability())
            robot.drive_differential_timed(
                left_pwm=100,
                right_pwm=95,
                duration_ms=500,
            )

        self.assertIn(
            {"N": 40, "L": 100, "R": 95, "T": 500, "H": "DMOVE"},
            transport.commands,
        )

    def test_differential_limits_are_checked_before_capability_or_write(self) -> None:
        transport = FakeTransport(differential_capability=True)
        robot = Robot(
            transport,
            response_timeout_seconds=0.1,
            motion_limits=MotionLimits(maximum_speed=100, maximum_duration_ms=500),
        )
        transport.open()

        with self.assertRaises(ValueError):
            robot.drive_differential_timed(
                left_pwm=101,
                right_pwm=100,
                duration_ms=500,
            )

        self.assertEqual(transport.commands, [])

    def test_simulated_transport_supports_end_to_end_api(self) -> None:
        settings = load_settings()
        robot = Robot.connect_simulated(settings)
        self.assertIsInstance(robot.transport, SimulatedTransport)

        with robot:
            snapshot = robot.read_telemetry()
            robot.drive_timed(
                MotionDirection.LEFT,
                speed=50,
                duration_ms=200,
            )

        simulated = robot.transport
        assert isinstance(simulated, SimulatedTransport)
        self.assertEqual(snapshot.line.left, 154)
        self.assertEqual(simulated.motion_history[0].direction, MotionDirection.LEFT)
        self.assertEqual(simulated.stop_count, 2)


if __name__ == "__main__":
    unittest.main()
