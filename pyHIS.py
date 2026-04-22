
import mmap
import struct
import numpy as np

__version__ = "0.2.0"


class _BaseHISFile:

    HEADER_FORMAT = "<2s H H H H H H i H H d i 30b"
    HEADER_SIZE = struct.calcsize(HEADER_FORMAT)  # 1 chunkはHEADER_SIZE + comment_length + image_size

    def __init__(self, path):
        self.path = None
        self.fd = None
        self.mm = None
        self.offsets = []
        self.open(path)

    def __len__(self):
        return len(self.offsets)

    def open(self, path):
        self.close()
        self.path = path
        self.fd = open(path, "rb")
        self.mm = mmap.mmap(self.fd.fileno(), 0, access=mmap.ACCESS_READ)
        self.update_offsets()

    def close(self):
        if self.mm is not None:
            self.mm.close()
            self.mm = None
        if self.fd is not None:
            self.fd.close()
            self.fd = None
        self.offsets = []

    def update_offsets(self):
        self.offsets = []
        offset = 0
        mm_len = len(self.mm)
        while offset + self.HEADER_SIZE <= mm_len:
            header = self.read_header(offset)
            if header[0] != b"IM":
                if offset == 0:
                    raise NotImplementedError(f"{self.path} is not HIS file (invalid magic code): {header[0]}")
                break
            if header[6] != 2:
                raise NotImplementedError("only 16bit type is supported")
            comment_length, width, height = header[1:4]
            image_size = width * height * 2
            chunk_size = self.HEADER_SIZE + comment_length + image_size
            if offset + chunk_size > mm_len:
                break
            self.offsets.append(offset)
            offset += chunk_size
            self.width = width
            self.height = height

    def read_header(self, offset):
        return struct.unpack_from(self.HEADER_FORMAT, self.mm, offset)

    def _frame_info(self, count):
        offset = self.offsets[count]
        header = self.read_header(offset)
        comment_length, width, height = header[1:4]
        image_offset = offset + self.HEADER_SIZE + comment_length
        return offset, comment_length, width, height, image_offset

    def _read_comment(self, offset, comment_length):
        comment_offset = offset + self.HEADER_SIZE
        return self.mm[comment_offset:comment_offset + comment_length].decode("utf-8").strip()


class HISFile(_BaseHISFile):
    """Safe HIS reader.

    Returned arrays are copied from the memory-mapped file, so the object can
    be used with `with` and closed safely while arrays remain referenced.
    """

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()
        return False

    def read_image(self, count, return_comment=False):
        offset, comment_length, width, height, image_offset = self._frame_info(count)
        image = np.frombuffer(buffer=self.mm,
                              dtype=np.uint16,
                              count=width*height,
                              offset=image_offset).reshape(height, width).copy()
        if return_comment:
            comment = self._read_comment(offset, comment_length)
            return image, comment
        return image

    def read_line(self, count, iy):
        _, comment_length, width, height, image_offset = self._frame_info(count)
        if not 0 <= iy < height:
            raise IndexError(f"line index out of range: {iy} not in [0, {height})")
        line_offset = image_offset + width * iy * 2
        line = np.frombuffer(buffer=self.mm,
                             dtype=np.uint16,
                             count=width,
                             offset=line_offset).copy()
        return line


class FastHISFile(_BaseHISFile):
    """High-throughput HIS reader.

    Returned arrays are zero-copy views into the memory-mapped file. Keep this
    object open while using those arrays, and do not use `with` if arrays may
    outlive the block.
    """

    def read_image(self, count, return_comment=False):
        offset, comment_length, width, height, image_offset = self._frame_info(count)
        image = np.frombuffer(buffer=self.mm,
                              dtype=np.uint16,
                              count=width*height,
                              offset=image_offset).reshape(height, width)
        if return_comment:
            comment = self._read_comment(offset, comment_length)
            return image, comment
        return image

    def read_line(self, count, iy):
        _, _, width, height, image_offset = self._frame_info(count)
        if not 0 <= iy < height:
            raise IndexError(f"line index out of range: {iy} not in [0, {height})")
        line_offset = image_offset + width * iy * 2
        line = np.frombuffer(buffer=self.mm,
                             dtype=np.uint16,
                             count=width,
                             offset=line_offset)
        return line

if __name__ == "__main__":
    from tqdm import trange
    import tifffile
    his = FastHISFile("a.his")
    image = None
    try:
        for i in trange(len(his)):
            image, comment = his.read_image(i, return_comment=True)
            tifffile.imwrite(f"img{i:04d}.tiff", image, imagej=True, metadata={"Info": comment})
    finally:
        image = None
        his.close()
