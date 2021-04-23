from _ctypes import Structure
from ctypes import c_uint64, c_uint32, c_uint16


class ImageMetadata(Structure):
    _pack_ = 1
    _fields_ = [("pulse_id", c_uint64),
                ("frame_index", c_uint64),
                ("daq_rec", c_uint32),
                ("is_good_image", c_uint16),
                ("image_y_size", c_uint32),
                ("image_x_size", c_uint32),
                ("bits_per_pixel", c_uint16)]

    def as_dict(self):
        return dict((f, getattr(self, f)) for f, _ in self._fields_)
