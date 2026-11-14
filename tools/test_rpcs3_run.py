"""Regression checks for RPCS3's mapped log behavior."""

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from rpcs3_run import read_log


class MappedLogTests(unittest.TestCase):
    def test_new_messages_inside_preallocated_space(self):
        with TemporaryDirectory() as folder:
            path = Path(folder) / "RPCS3.log"
            path.write_bytes(b"boot\n" + b"\0" * 4096)
            first, cursor = read_log(path, 0)
            self.assertEqual(first, b"boot\n")
            self.assertEqual(read_log(path, cursor), (b"", cursor))
            with path.open("r+b") as stream:
                stream.seek(cursor)
                stream.write(b"controller ready\n")
            second, cursor = read_log(path, cursor)
            self.assertEqual(second, b"controller ready\n")
            self.assertEqual(cursor, len(first + second))

    def test_truncated_log_starts_again(self):
        with TemporaryDirectory() as folder:
            path = Path(folder) / "RPCS3.log"
            path.write_bytes(b"first invocation\n")
            _, cursor = read_log(path, 0)
            path.write_bytes(b"new\n")
            self.assertEqual(read_log(path, cursor), (b"new\n", 4))

    def test_written_region_spans_read_blocks(self):
        with TemporaryDirectory() as folder:
            path = Path(folder) / "RPCS3.log"
            text = b"x" * (1024 * 1024 + 51)
            path.write_bytes(text + b"\0" * 8192)
            self.assertEqual(read_log(path, 0), (text, len(text)))


if __name__ == "__main__":
    unittest.main()
