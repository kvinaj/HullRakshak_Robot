"""Encoding and decoding for the ELEGOO Conqueror serial protocol."""

from __future__ import annotations

import json
import re
from collections.abc import Mapping


LABELED_INTEGER = re.compile(r"^(?P<label>[A-Za-z0-9]+)_(?P<value>-?\d+)$")


def encode_command(
    command_number: int,
    *,
    request_id: str | None = None,
    parameters: Mapping[str, int | str] | None = None,
) -> bytes:
    """Return one compact JSON command framed by braces."""
    command: dict[str, int | str] = {"N": command_number}
    if parameters:
        command.update(parameters)
    if request_id is not None:
        command["H"] = request_id
    return json.dumps(command, separators=(",", ":")).encode("ascii")


def parse_labeled_integer(frame: str, expected_label: str) -> int | None:
    """Parse ``LABEL_integer`` and ignore unrelated protocol frames."""
    match = LABELED_INTEGER.fullmatch(frame)
    if not match or match.group("label") != expected_label:
        return None
    return int(match.group("value"))


class FrameDecoder:
    """Incrementally split a serial byte stream into ``{...}`` frames."""

    def __init__(self) -> None:
        self._inside_frame = False
        self._buffer: list[str] = []

    def feed(self, data: bytes | str) -> list[str]:
        text = data.decode("ascii", errors="ignore") if isinstance(data, bytes) else data
        frames: list[str] = []

        for character in text:
            if character == "{":
                self._inside_frame = True
                self._buffer.clear()
            elif character == "}" and self._inside_frame:
                frames.append("".join(self._buffer))
                self._inside_frame = False
                self._buffer.clear()
            elif self._inside_frame:
                self._buffer.append(character)

        return frames
