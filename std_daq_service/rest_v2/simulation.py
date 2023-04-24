import logging
import threading
from threading import Event

from std_daq_service.det_udp_simulator.gigafrost import GFUdpPacketGenerator
from std_daq_service.det_udp_simulator.udp_stream import generate_udp_stream

_logger = logging.getLogger("StartStopRestManager")

DETECTOR_GF = 'gigafrost'
DETECTOR_JF = 'jungfrau'
DETECTOR_EG = 'eiger'


class SimulationRestManager(object):
    def __init__(self, daq_config):
        self.daq_config = daq_config

        detector_type = self.daq_config['detector_type']
        height = self.daq_config['image_pixel_height']
        width = self.daq_config['image_pixel_width']
        bit_depth = self.daq_config['bit_depth']

        self._image_size_bytes = height * width * bit_depth / 8

        if detector_type == DETECTOR_GF:
            self.generator = GFUdpPacketGenerator(image_pixel_height=height, image_pixel_width=width)
        else:
            raise ValueError(f"Unknown detector type: {detector_type}.")

        self.stop_event = Event()

        self._generator_thread = None
        self.status = 'READY'
        self.bytes_per_second = 0
        self.images_per_second = 0

    def _simulation(self):
        start_udp_port = self.daq_config['start_udp_port']
        self.status = 'STREAMING'
        generate_udp_stream(self.generator, '0.0.0.0', start_udp_port,
                            stop_event=self.stop_event, image_callback=self._image_callback)
        self.status = 'READY'

    def _image_callback(self, i_image):
        self.images_per_second += 1
        self.bytes_per_second += self._image_size_bytes

    def start(self):
        self.stop_event.clear()
        self._generator_thread = threading.Thread(target=self._simulation)
        self._generator_thread.start()

        return self.get_status()

    def stop(self):
        self.stop_event.set()
        if self._generator_thread is not None:
            self._generator_thread.join()

        self.status = 'READY'
        self._generator_thread = None
        self.bytes_per_second = 0
        self.images_per_second = 0

        return self.get_status()

    def get_status(self):
        return {
            'status': self.status,
            'stats': {'bytes_per_second': self.bytes_per_second,
                      'images_per_second': self.images_per_second}
        }

    def close(self):
        self.stop()
