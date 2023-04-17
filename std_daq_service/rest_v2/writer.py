import logging

import cv2
import numpy as np
import zmq

from std_daq_service.writer_driver.start_stop_driver import WriterDriver
from utils import update_config

_logger = logging.getLogger("StartStopRestManager")


class WriterRestManager(object):
    def __init__(self, writer_driver: WriterDriver):
        self.writer_driver = writer_driver

    def write_sync(self, output_file, n_images):
        writer_status = self.writer_driver.get_state()
        if writer_status['state'] != "READY":
            raise RuntimeError('Cannot start writing until writer state is READY. '
                               'Stop the current acquisition or wait for it to finish.')

        return self.get_status()

    def write_async(self, output_file, n_images):
        state = self.writer_driver.get_state()
        if state['state'] != "READY":
            raise RuntimeError('Cannot start writing until writer state is READY. '
                               'Stop the current acquisition or wait for it to finish.')

        return self.get_status()

    def stop_writing(self):
        self.writer_driver.stop()

        return self.get_status()

    def get_status(self):
        return self.writer_driver.get_status()

    def close(self):
        _logger.info("Shutting down manager.")
        self.writer_driver.close()


def generate_mjpg_image_stream(ctx, image_stream_url):
    socket = ctx.socket(zmq.SUB)
    socket.setsockopt(zmq.SUBSCRIBE, b'')
    socket.connect(image_stream_url)

    while True:
        json_header = socket.recv_json()
        image_bytes = socket.recv()

        image_width = json_header['width']
        image_height = json_header['height']
        dtype = json_header['dtype']

        # interpret the byte array as a NumPy array
        image_array = np.frombuffer(image_bytes, dtype=dtype).reshape(image_height, image_width)

        # convert the uint16 grayscale image to uint8 (0-255)
        image_array = (image_array // 256).astype(np.uint8)
        image_array = cv2.resize(image_array, (640, 480))
        image_array = cv2.applyColorMap(image_array, cv2.COLORMAP_JET)

        # encode the color image as JPEG
        _, buffer = cv2.imencode('.jpg', image_array)
        image_bytes = buffer.tobytes()

        # yield the frame for the MJPG stream
        yield b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + image_bytes + b'\r\n'
