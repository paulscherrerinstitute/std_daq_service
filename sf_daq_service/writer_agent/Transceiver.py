import logging
from _ctypes import Structure
from ctypes import c_uint64, c_uint32
from threading import Thread
import zmq

_logger = logging.getLogger('BufferAgent')


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


class StoreStreamMessage(Structure):
    _pack_ = 1
    _fields_ = [("image_meta", ImageMetadata),
                ("writer_meta", WriteMetadata)]


class Transceiver(object):
    def __init__(self, input_stream_url, output_stream_url, processing_func):
        self.input_stream_url = input_stream_url
        self.output_stream_url = output_stream_url
        self.processing_func = processing_func

        self.last_run_id = None

        transceiver_thread = Thread(target=self.run_transceiver)
        transceiver_thread.daemon = True
        transceiver_thread.start()

    def run_transceiver(self):
        ctx = zmq.Context()

        _logger.info(f'Connecting input stream to {self.input_stream_url}.')
        input_stream = ctx.socket(zmq.SUB)
        input_stream.connect(self.input_stream_url)
        input_stream.setsockopt(zmq.SUBSCRIBE, '')

        _logger.info(f'Binding output stream to {self.output_stream_url}.')
        output_stream = ctx.socket(zmq.PUB)
        output_stream.bind(self.output_stream_url)

        while True:
            image_metadata = input_stream.recv()

            message = self.processing_func(image_metadata)

            if message:
                output_stream.send(message)
