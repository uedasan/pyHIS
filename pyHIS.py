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

    # def __enter__(self):
    #     return self

    # def __exit__(self, ex_type, ex_value, trace):
    #     self.close()

    def open(self, path):
        self.path = path
        self.fd = open(path, "rb")
        self.mm = mmap.mmap(self.fd.fileno(), 0, access=mmap.ACCESS_READ)
        self.update_offsets()

    def close(self):
        # bug: read_imageでcopy=Falseの場合、imageを破棄しないとcloseできない
        self.mm.close()
        self.fd.close()

    def update_offsets(self):
        self.offsets = []
        offset = 0
        while offset < len(self.mm):
            self.offsets.append(offset)
            header = self.read_header(offset)
            if header[0] != b"IM":
                raise NotImplementedError(f"{self.path} is not HIS file (invalid magic code)")
            if header[6] != 2:
                raise NotImplementedError("only 16bit type is supported")
            comment_length, width, height = header[1:4]
            image_size = width * height * 2
            offset += self.HEADER_SIZE + comment_length + image_size
            self.width = width
            self.height = height

    def read_header(self, offset):
        return struct.unpack_from(self.HEADER_FORMAT, self.mm, offset)

    def read_image(self, count, copy=False):
        offset = self.offsets[count]
        header = self.read_header(offset)
        comment_length, width, height = header[1:4]
        image_offset = offset + self.HEADER_SIZE + comment_length
        image = np.frombuffer(buffer=self.mm,
                              dtype=np.uint16,
                              count=width*height,
                              offset=image_offset).reshape(height, width)
        if copy:
            return image.copy()
        else:
            return image


if __name__=="__main__":
    from skimage.io import imsave
    from tqdm import trange
    his = HISFile("a.his")
    s = 0
    for i in trange(len(his)):
        image = his.read_image(i)
        s += np.mean(image)
