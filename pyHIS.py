
import mmap
import struct
import numpy as np

class HISFile:

    HEADER_FORMAT = "<2s H H H H H H i H H d i 30b"
    HEADER_SIZE = struct.calcsize(HEADER_FORMAT)  # 1 chunkはHEADER_SIZE + comment_length + image_size

    def __init__(self, path):
        self.open(path)

    def __len__(self):
        return len(self.offsets)

    def open(self, path):
        self.path = path
        self.fd = open(path, "rb")
        self.mm = mmap.mmap(self.fd.fileno(), 0, access=mmap.ACCESS_READ)
        self.update_offsets()

    def close(self):
        self.mm.close()
        self.fd.close()

    def update_offsets(self):
        self.offsets = []
        offset = 0
        while offset < len(self.mm):
            self.offsets.append(offset)
            header = self.read_header(offset)
            if header[0] != b"IM":
                if offset == 0:
                    raise NotImplementedError(f"{self.path} is not HIS file (invalid magic code): {header[0]}")
                break
            if header[6] != 2:
                raise NotImplementedError("only 16bit type is supported")
            comment_length, width, height = header[1:4]
            image_size = width * height * 2
            offset += self.HEADER_SIZE + comment_length + image_size
            self.width = width
            self.height = height

    def read_header(self, offset):
        return struct.unpack_from(self.HEADER_FORMAT, self.mm, offset)

    def read_image(self, count, return_comment=False):
        offset = self.offsets[count]
        header = self.read_header(offset)
        comment_length, width, height = header[1:4]
        image_offset = offset + self.HEADER_SIZE + comment_length
        image = np.frombuffer(buffer=self.mm,
                              dtype=np.uint16,
                              count=width*height,
                              offset=image_offset).reshape(height, width)
        if return_comment:
            comment_offset = offset + self.HEADER_SIZE
            comment = self.mm[comment_offset:comment_offset + comment_length].decode('utf-8').strip()
            return image, comment
        return image

    def read_line(self, count, iy):
        offset = self.offsets[count]
        header = self.read_header(offset)
        comment_length, width, height = header[1:4]
        image_offset = offset + self.HEADER_SIZE + comment_length
        line_offset = image_offset + width * iy * 2
        line = np.frombuffer(buffer=self.mm,
                             dtype=np.uint16,
                             count=width,
                             offset=line_offset)
        return line

if __name__ == "__main__":
    from tqdm import trange
    import tifffile
    his = HISFile("a.his")
    for i in trange(len(his)):
        image, comment = his.read_image(i, return_comment=True)
        tifffile.imwrite(f"img{i:04d}.tiff", image, imagej=True, metadata={"Info": comment})