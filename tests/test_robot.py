import json
import unittest

from hullrakshak.robot import Robot


class FakeTransport:
    VALUES = {"L": 181, "M": 193, "R": 73, "U": 42}

    def __init__(self) -> None:
        self.is_open = False
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
        if request_id in self.VALUES:
            self.responses.append(f"{request_id}_{self.VALUES[request_id]}")

    def read_frame(self, timeout_seconds: float) -> str:
        if not self.responses:
            raise TimeoutError
        return self.responses.pop(0)


class RobotTests(unittest.TestCase):
    def test_read_telemetry_uses_sensor_protocol(self) -> None:
        transport = FakeTransport()
        robot = Robot(transport, response_timeout_seconds=0.1)

        with robot:
            snapshot = robot.read_telemetry()

        self.assertEqual(snapshot.line.left, 181)
        self.assertEqual(snapshot.line.middle, 193)
        self.assertEqual(snapshot.line.right, 73)
        self.assertEqual(snapshot.ultrasonic_cm, 42)
        self.assertEqual(transport.commands[0], {"N": 100})
        self.assertEqual(transport.commands[-1], {"N": 100})


if __name__ == "__main__":
    unittest.main()
