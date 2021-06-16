from _ctypes import Structure
from ctypes import c_uint32, c_uint64, c_uint16


class ImageMetadata(Structure):
    _pack_ = 1
    _fields_ = [("signature", c_uint32),
                ("version", c_uint32),

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