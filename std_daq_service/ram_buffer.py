import logging
from multiprocessing.shared_memory import SharedMemory

import numpy as np

_logger = logging.getLogger("RamBuffer")

class RamBuffer:
    def __init__(self, channel_name, shape, dtype, data_n_bytes, n_slots, compression=None):
        compression_text = 'image' if compression is None else 'compressed'
        self.buffer_name = f'{channel_name}-{compression_text}'

        self.shape = tuple(shape)
        self.dtype = dtype

        self.n_slots = n_slots
        self.data_bytes = data_n_bytes
        self.buffer_bytes = self.data_bytes * self.n_slots

        _logger.info(f"Opening buffer_name {self.buffer_name} with n_slots {self.n_slots} "
                     f"for data_bytes {self.data_bytes}")

        self.shm = None
        self.buffer = None

        try:
            self.shm = SharedMemory(name=self.buffer_name, create=False, size=self.buffer_bytes)
        except FileNotFoundError:
            _logger.error("SharedMemory failed: %s not found", self.buffer_name)
            raise

    def __del__(self):
        if self.shm:
            self.shm.unlink()

    def write(self, image_id, src_data):
        dst_data = self.get_data(image_id)

        if src_data is not None:
            dst_data[:len(src_data)] = src_data

    def get_data(self, image_id):
        offset = int((image_id % self.n_slots) * self.data_bytes)
        return np.ndarray(self.shape, dtype=self.dtype, buffer=self.shm.buf, offset=offset)
