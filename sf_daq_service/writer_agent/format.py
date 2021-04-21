from _ctypes import Structure
from ctypes import c_uint64, c_uint32


class ImageMetadata(Structure):
    _pack_ = 1
    _fields_ = [("pulse_id", c_uint64),
                ("frame_index", c_uint64),
                ("daq_rec", c_uint32),
                ("is_good_image", c_uint32)]


class WriteMetadata(Structure):
    _pack_ = 1
    _fields_ = [("run_id", c_uint64),
                ("i_image", c_uint32),
                ("n_image", c_uint32),
                ("image_y_size", c_uint32),
                ("image_x_size", c_uint32),
                ("bits_per_pixel", c_uint32)]


class WriterStreamMessage(Structure):
    _pack_ = 1
    _fields_ = [("image_meta", ImageMetadata),
                ("write_meta", WriteMetadata)]
