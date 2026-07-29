import unittest

from hullrakshak.protocol import (
    FrameDecoder,
    encode_command,
    parse_labeled_integer,
)


class ProtocolTests(unittest.TestCase):
    def test_encode_command_is_compact_and_ordered(self) -> None:
        encoded = encode_command(
            22,
            request_id="M",
            parameters={"D1": 1},
        )
        self.assertEqual(encoded, b'{"N":22,"D1":1,"H":"M"}')

    def test_decoder_handles_fragmented_and_concatenated_frames(self) -> None:
        decoder = FrameDecoder()
        self.assertEqual(decoder.feed(b"noise{L_1"), [])
        self.assertEqual(decoder.feed(b"81}{M_193}{R"), ["L_181", "M_193"])
        self.assertEqual(decoder.feed(b"_73}"), ["R_73"])

    def test_parse_labeled_integer_ignores_unrelated_frames(self) -> None:
        self.assertEqual(parse_labeled_integer("M_193", "M"), 193)
        self.assertIsNone(parse_labeled_integer("L_181", "M"))
        self.assertIsNone(parse_labeled_integer("ok", "M"))


if __name__ == "__main__":
    unittest.main()
