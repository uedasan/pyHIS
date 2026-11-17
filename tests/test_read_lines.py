import struct
import tempfile
import unittest
from pathlib import Path

import numpy as np

from pyHIS import FastHISFile, HISFile


class ReadLinesTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.path = Path(folder.name) / "rows.his"
        self.first = np.arange(24, dtype=np.uint16).reshape(6, 4)
        self.second = (100 + np.arange(15, dtype=np.uint16)).reshape(5, 3)
        with self.path.open("wb") as stream:
            for frame in (self.first, self.second):
                height, width = frame.shape
                comment = b"row block"
                stream.write(struct.pack(HISFile.HEADER_FORMAT, b"IM", len(comment),
                                         width, height, 0, 0, 2, 0, 0, 0, 0, 0,
                                         *([0] * 30)))
                stream.write(comment)
                stream.write(frame.astype("<u2").tobytes())

    def test_copy_survives_close(self):
        with HISFile(self.path) as his:
            block = his.read_lines(1, 0, 5, step=2)
            full_height = his.read_lines(0, 0, 6)
            empty = his.read_lines(1, 5, 5)
        np.testing.assert_array_equal(block, self.second[::2])
        np.testing.assert_array_equal(full_height, self.first)
        self.assertEqual(empty.shape, (0, 3))
        self.assertTrue(block.flags.c_contiguous)

    def test_fast_reader_returns_a_view(self):
        his = FastHISFile(self.path)
        try:
            image = his.read_image(0)
            block = his.read_lines(0, 1, 6, 2)
            try:
                np.testing.assert_array_equal(block, self.first[1:6:2])
                self.assertTrue(np.shares_memory(block, image))
                self.assertFalse(block.flags.writeable)
            finally:
                del block, image
        finally:
            his.close()

    def test_invalid_rows_and_steps(self):
        with HISFile(self.path) as his:
            for start, stop in ((-1, 3), (0, 7), (4, 2)):
                with self.subTest(start=start, stop=stop), self.assertRaises(IndexError):
                    his.read_lines(0, start, stop)
            for step in (0, -1):
                with self.subTest(step=step), self.assertRaises(ValueError):
                    his.read_lines(0, 0, 3, step)


if __name__ == "__main__":
    unittest.main()
