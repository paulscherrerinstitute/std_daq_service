import logging
import threading
from threading import Event

from std_daq_service.det_udp_simulator.gigafrost import GFUdpPacketGenerator

_logger = logging.getLogger("StartStopRestManager")

DETECTOR_GF = 'gigafrost'
DETECTOR_JF = 'jungfrau'
DETECTOR_EG = 'eiger'


class SimulationRestManager(object):
    def __init__(self, detector_type):
        if detector_type == DETECTOR_GF:
            self.generator = GFUdpPacketGenerator(image_pixel_height=2016, image_pixel_width=2016, image_filename=None)
        else:
            raise ValueError(f"Unknown detector type: {detector_type}.")

        self.stop_event = Event()
        self._generator_thread = threading.Thread()

    def start(self, n_images=None):
        pass

    def stop(self):
        pass

    def get_status(self):
        pass

    def close(self):
        _logger.info("Shutting down manager.")
        self.driver.close()


