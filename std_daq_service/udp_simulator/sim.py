import logging
import threading
from threading import Event

from std_daq_service.udp_simulator.udp_stream import generate_udp_stream
from std_daq_service.udp_simulator.util import get_detector_generator

_logger = logging.getLogger("StartStopRestManager")

DETECTOR_GF = 'gigafrost'
DETECTOR_JF = 'jungfrau'
DETECTOR_EG = 'eiger'


class SimulationRestManager(object):
    def __init__(self, daq_config, output_ip, image_filename=None):
        self.daq_config = daq_config
        self.output_ip = output_ip

        detector_type = self.daq_config['detector_type']
        height = self.daq_config['image_pixel_height']
        width = self.daq_config['image_pixel_width']
        bit_depth = self.daq_config['bit_depth']
        n_modules = self.daq_config['n_modules']
        modules_info = self.daq_config.get('submodule_info', None)

        self._image_size_bytes = height * width * bit_depth / 8

        self.generator = get_detector_generator(detector_type, height, width, bit_depth, n_modules, modules_info, image_filename=image_filename)
        self.stop_event = Event()

        self._generator_thread = None
        self.status = 'READY'
        self.n_generated_images = 0

    def _simulation(self):
        start_udp_port = self.daq_config['start_udp_port']
        self.status = 'STREAMING'
        generate_udp_stream(self.generator, self.output_ip, start_udp_port,
                            stop_event=self.stop_event, image_callback=self._image_callback)
        self.status = 'READY'

    def _image_callback(self, i_image):
        self.n_generated_images += 1

    def start(self):
        self.stop()
        self.n_generated_images = 0

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

        return self.get_status()

    def get_status(self):
        return {
            'status': self.status,
            'stats': {'n_generated_images': self.n_generated_images}
        }

    def close(self):
        self.stop()
