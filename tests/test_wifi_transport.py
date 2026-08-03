import socket
import unittest
from unittest.mock import patch

from hullrakshak.settings import WifiSettings
from hullrakshak.transport.wifi import WifiTransport


class FakeSocket:
    def __init__(self) -> None:
        self.received_chunks = [b"{Heartbeat}{M_193}"]
        self.sent: list[bytes] = []
        self.closed = False

    def settimeout(self, timeout: float) -> None:
        pass

    def recv(self, size: int) -> bytes:
        if self.received_chunks:
            return self.received_chunks.pop(0)
        raise socket.timeout

    def sendall(self, data: bytes) -> None:
        self.sent.append(data)

    def shutdown(self, how: int) -> None:
        self.closed = True

    def close(self) -> None:
        self.closed = True


class WifiTransportTests(unittest.TestCase):
    def test_echoes_heartbeat_and_queues_other_frames(self) -> None:
        fake_socket = FakeSocket()

        transport = WifiTransport(
            WifiSettings(
                host="192.168.4.1",
                port=100,
                connect_timeout_seconds=1.0,
                response_timeout_seconds=1.0,
            )
        )
        with patch("socket.create_connection", return_value=fake_socket):
            transport.open()
            try:
                self.assertEqual(transport.read_frame(1.0), "M_193")
            finally:
                transport.close()

        self.assertEqual(fake_socket.sent, [b"{Heartbeat}"])
        self.assertTrue(fake_socket.closed)


if __name__ == "__main__":
    unittest.main()
