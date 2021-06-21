from _ctypes import Structure
from ctypes import c_uint64, c_uint16

image_metadata_dtype_mapping = {
    1: 'uint8',
    2: 'uint16',
    4: 'uint32',
    8: 'uint64',
    12: 'float16',
    14: 'float32',
    18: 'float64'
}

image_metadata_encoding_mapping = {
    0: 'raw',
    1: 'bshuffle_lz4'
}


class ImageMetadata(Structure):
    _pack_ = 1
    _fields_ = [
                ("version", c_uint64),
                ("id", c_uint64),
                ("height", c_uint64),
                ("width", c_uint64),

                ("dtype", c_uint16),
                ("encoding", c_uint16),
                ("source_id", c_uint16),
                ("status", c_uint16),

                ("user_1", c_uint64),
                ("user_2", c_uint64)]

    def as_dict(self):
        return dict((f, getattr(self, f)) for f, _ in self._fields_)
