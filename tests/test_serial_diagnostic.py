import unittest

from hullrakshak.applications.serial_diagnostic import (
    MOVEMENT_BYTES,
    STOP_BYTES,
    BraceFrameCapture,
    run_diagnostic,
)
from hullrakshak.settings import SerialSettings


class FakeSerial:
    def __init__(self) -> None:
        self.is_open = True
        self.in_waiting = 0
        self.writes: list[bytes] = []
        self.input_reset = False

    def write(self, data: bytes) -> int:
        self.writes.append(data)
        return len(data)

    def flush(self) -> None:
        pass

    def read(self, size: int = 1) -> bytes:
        return b""

    def reset_input_buffer(self) -> None:
        self.input_reset = True

    def close(self) -> None:
        self.is_open = False


class SerialDiagnosticTests(unittest.TestCase):
    def setUp(self) -> None:
        self.settings = SerialSettings(
            port="/dev/fake",
            baudrate=9600,
            reset_delay_seconds=6.0,
            response_timeout_seconds=2.5,
        )

    def test_exact_command_bytes(self) -> None:
        self.assertEqual(
            MOVEMENT_BYTES,
            b'{"N":2,"D1":3,"D2":80,"T":500,"H":"MOVE"}',
        )
        self.assertEqual(STOP_BYTES, b'{"N":100}')

    def test_normal_run_starts_and_ends_with_stop(self) -> None:
        connection = FakeSerial()
        delays: list[float] = []
        events: list[tuple[str, bytes]] = []

        run_diagnostic(
            self.settings,
            serial_factory=lambda *args, **kwargs: connection,
            sleep=delays.append,
            observer=lambda *args, **kwargs: None,
            event_writer=lambda kind, data: events.append((kind, data)),
        )

        self.assertEqual(delays, [6.0])
        self.assertTrue(connection.input_reset)
        self.assertEqual(
            connection.writes,
            [STOP_BYTES, MOVEMENT_BYTES, STOP_BYTES],
        )
        self.assertEqual(events, [("TX", data) for data in connection.writes])
        self.assertFalse(connection.is_open)

    def test_exception_during_observation_still_sends_stop(self) -> None:
        connection = FakeSerial()

        def fail_observation(*args: object, **kwargs: object) -> None:
            raise RuntimeError("diagnostic failure")

        with self.assertRaisesRegex(RuntimeError, "diagnostic failure"):
            run_diagnostic(
                self.settings,
                serial_factory=lambda *args, **kwargs: connection,
                sleep=lambda seconds: None,
                observer=fail_observation,
                event_writer=lambda kind, data: None,
            )

        self.assertEqual(
            connection.writes,
            [STOP_BYTES, MOVEMENT_BYTES, STOP_BYTES],
        )
        self.assertFalse(connection.is_open)

    def test_keyboard_interrupt_during_observation_still_sends_stop(self) -> None:
        connection = FakeSerial()

        def interrupt_observation(*args: object, **kwargs: object) -> None:
            raise KeyboardInterrupt

        with self.assertRaises(KeyboardInterrupt):
            run_diagnostic(
                self.settings,
                serial_factory=lambda *args, **kwargs: connection,
                sleep=lambda seconds: None,
                observer=interrupt_observation,
                event_writer=lambda kind, data: None,
            )

        self.assertEqual(
            connection.writes,
            [STOP_BYTES, MOVEMENT_BYTES, STOP_BYTES],
        )
        self.assertFalse(connection.is_open)

    def test_frame_capture_preserves_split_and_adjacent_frames(self) -> None:
        capture = BraceFrameCapture()

        self.assertEqual(capture.feed(b"noise{MOVE"), [])
        self.assertEqual(
            capture.feed(b"_ok}{ok}tail"),
            [b"{MOVE_ok}", b"{ok}"],
        )


if __name__ == "__main__":
    unittest.main()
