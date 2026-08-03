"""ESP32 TCP transport with automatic factory-heartbeat handling."""

from __future__ import annotations

import queue
import socket
import threading

from hullrakshak.protocol import FrameDecoder
from hullrakshak.settings import WifiSettings
from hullrakshak.transport.base import RobotConnectionError


class WifiTransport:
    """Communicate through the ESP32 bridge on TCP port 100."""

    def __init__(self, settings: WifiSettings) -> None:
        self.settings = settings
        self._socket: socket.socket | None = None
        self._frames: queue.Queue[str | BaseException] = queue.Queue()
        self._write_lock = threading.Lock()
        self._reader_thread: threading.Thread | None = None
        self._closing = threading.Event()

    @property
    def is_open(self) -> bool:
        return self._socket is not None and not self._closing.is_set()

    def open(self) -> None:
        if self.is_open:
            return
        self._closing.clear()
        try:
            self._socket = socket.create_connection(
                (self.settings.host, self.settings.port),
                timeout=self.settings.connect_timeout_seconds,
            )
            self._socket.settimeout(0.5)
        except OSError as error:
            self._socket = None
            raise RobotConnectionError(
                f"Could not connect to robot Wi-Fi at "
                f"{self.settings.host}:{self.settings.port}: {error}"
            ) from error

        self._reader_thread = threading.Thread(
            target=self._reader_loop,
            name="robot-wifi-reader",
            daemon=True,
        )
        self._reader_thread.start()

    def close(self) -> None:
        self._closing.set()
        connection = self._socket
        self._socket = None
        if connection is not None:
            try:
                connection.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            connection.close()
        if self._reader_thread is not None:
            self._reader_thread.join(timeout=1.0)
            self._reader_thread = None

    def write(self, data: bytes) -> None:
        connection = self._socket
        if connection is None or self._closing.is_set():
            raise RobotConnectionError("Robot Wi-Fi connection is not open")
        try:
            with self._write_lock:
                connection.sendall(data)
        except OSError as error:
            raise RobotConnectionError(
                f"Robot Wi-Fi write failed: {error}"
            ) from error

    def read_frame(self, timeout_seconds: float) -> str:
        try:
            item = self._frames.get(timeout=timeout_seconds)
        except queue.Empty as error:
            raise TimeoutError(
                f"No complete robot response within {timeout_seconds:.1f}s"
            ) from error
        if isinstance(item, BaseException):
            raise RobotConnectionError(f"Robot Wi-Fi connection failed: {item}")
        return item

    def _reader_loop(self) -> None:
        decoder = FrameDecoder()
        connection = self._socket
        if connection is None:
            return

        while not self._closing.is_set():
            try:
                data = connection.recv(4096)
                if not data:
                    if not self._closing.is_set():
                        self._frames.put(
                            ConnectionError("ESP32 closed the TCP connection")
                        )
                    return
            except socket.timeout:
                continue
            except OSError as error:
                if not self._closing.is_set():
                    self._frames.put(error)
                return

            for frame in decoder.feed(data):
                if frame == "Heartbeat":
                    try:
                        self.write(b"{Heartbeat}")
                    except RobotConnectionError as error:
                        self._frames.put(error)
                        return
                else:
                    self._frames.put(frame)
