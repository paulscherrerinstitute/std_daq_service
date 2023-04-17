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
        writer_status = self.writer_driver.get_status()
        if writer_status['state'] != "READY":
            raise RuntimeError('Cannot start writing until writer state is READY. '
                               'Stop the current acquisition or wait for it to finish.')

        return self.get_status()

    def write_async(self, output_file, n_images):
        state = self.writer_driver.get_status()
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

