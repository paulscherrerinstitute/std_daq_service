import logging
from _ctypes import Structure
from ctypes import c_uint64, c_uint32
from threading import Thread
import zmq

_logger = logging.getLogger('BufferAgent')

OP_CONTINUE = 0
OP_START = 1
OP_END = 2


class ImageMetadata(Structure):
    _pack_ = 1
    _fields_ = [("pulse_id", c_uint64),
                ("frame_index", c_uint64),
                ("daq_rec", c_uint32),
                ("is_good_image", c_uint32)]


class StoreStream(Structure):
    _pack_ = 1
    _fields_ = [("image_metadata", ImageMetadata),
                ("run_id", c_uint64),
                ("i_image", c_uint32),
                ("n_image", c_uint32),
                ("image_y_size", c_uint32),
                ("image_x_size", c_uint32),
                ("op_code", c_uint32),
                ("bits_per_pixel", c_uint32)]


class Transceiver(object):
    def __init__(self, input_stream_url, output_stream_url, processing_func):
        self.input_stream_url = input_stream_url
        self.output_stream_url = output_stream_url
        self.processing_func = processing_func

        self.last_run_id = None

        transceiver_thread = Thread(target=self.run_transceiver)
        transceiver_thread.daemon = True
        transceiver_thread.start()

    def start_run(self, output_stream, start_stream_request):
        # End run message resets the state of the writer before sending a write request.
        # In case the writer is not in the expected state, this fixes it.
        self.end_run()

        _logger.info(f'Sending start run_id {start_stream_request.run_id}.')
        output_stream.send(start_stream_request)

        self.last_run_id = start_stream_request.run_id

    def end_run(self, output_stream, stop_stream_request):
        _logger.info(f'Sending stop run_id {self.last_run_id}.')
        output_stream.send(stop_stream_request)

        self.last_run_id = None

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

            op_code, store_metadata = self.processing_func(image_metadata)

            if op_code == OP_START:
                self.start_run(output_stream, store_metadata)

            if store_metadata:
                output_stream.send(store_metadata)

            if op_code == OP_END:
                self.end_run(output_stream, store_metadata)
