import logging
import requests
from pcaspy import Driver

from std_daq_service.rest_v2.rest import WRITE_ASYNC_ENDPOINT, STOP_ENDPOINT, CONFIG_ENDPOINT, \
    STATUS_ENDPOINT, DAQ_CONFIG_FIELDS

_logger = logging.getLogger("EpicsStartStopRestDriver")

PV_NAME_APPLY_CONFIG = 'CMD_APPLY_CONFIG'
PV_NAME_START_WRITING = 'CMD_START_WRITING'
PV_NAME_STOP_WRITING = 'CMD_STOP_WRITING'
PV_NAME_GET_STATUS = 'CMD_GET_STATUS'
PV_NAME_GET_CONFIG = 'CMD_GET_CONFIG'


class EpicsStartStopRestDriver(Driver):

    def __init__(self, rest_url):
        super(EpicsStartStopRestDriver, self).__init__()
        self.rest_url = rest_url

    def read(self, reason):
        if reason == PV_NAME_GET_STATUS:
            self._get_status()
            value = 1
        elif reason == PV_NAME_GET_CONFIG:
            self._get_config()
            value = 1
        else:
            value = self.getParam(reason)

        return value

    def write(self, reason, value):
        if reason == PV_NAME_APPLY_CONFIG:
            n_images = self.getParam('n_images')
            output_file = self.getParam('output_file')
            self._set_config(n_images=n_images, output_file=output_file)

        elif reason == PV_NAME_START_WRITING:
            n_images = self.getParam('n_images')
            output_file = self.getParam('output_file')
            self._write_async(n_images=n_images, output_file=output_file)

        elif reason == PV_NAME_STOP_WRITING:
            self._stop()

        else:
            self.setParam(reason, value)

    def _set_config(self):
        json_data = {key: self.getParam(key) for key in DAQ_CONFIG_FIELDS}
        response = requests.post(url=f"{self.rest_url}{CONFIG_ENDPOINT}", json=json_data)
        self._process_config_response(response)

    def _get_config(self):
        response = requests.get(url=f"{self.rest_url}{CONFIG_ENDPOINT}")
        self._process_config_response(response)

    def _write_async(self, n_images, output_file):
        json_data = {"n_images": n_images, "output_file": output_file}
        response = requests.post(url=f"{self.rest_url}{WRITE_ASYNC_ENDPOINT}", json=json_data)
        self._process_writer_response(response)

    def _stop(self):
        response = requests.post(url=f"{self.rest_url}{STOP_ENDPOINT}")
        self._process_writer_response(response)

    def _get_status(self):
        response = requests.get(url=f"{self.rest_url}{STATUS_ENDPOINT}")
        self._process_writer_response(response)

    def _process_writer_response(self, response):
        main_json = response.json()
        writer_json = main_json['writer']

        self.setParam('writer_state', writer_json['state'])
        self.setParam('writer_message', main_json['message'])

        self.setParam('acq_state', writer_json['acquisition']['state'])

        self.setParam('acq_n_images', writer_json['acquisition']['info'].get('n_images', 0))
        self.setParam('acq_output_file', writer_json['acquisition']['info'].get('output_file', ""))

        self.setParam('acq_n_writes_complete', writer_json['acquisition']['stats'].get('n_writes_complete', 0))
        self.setParam('acq_n_writes_requested', writer_json['acquisition']['stats'].get('n_writes_requested', 0))
        self.setParam('acq_start_time', writer_json['acquisition']['stats'].get('start_time', 0))
        self.setParam('acq_stop_time', writer_json['acquisition']['stats'].get('stop_time', 0))

    def _process_config_response(self, response):
        config_json = response.json()['config']
        
        self.setParam('bit_depth', config_json['bit_depth'])
        self.setParam('detector_name', config_json['detector_name'])
        self.setParam('detector_type', config_json['detector_type'])
        self.setParam('image_pixel_height', config_json['image_pixel_height'])
        self.setParam('image_pixel_width', config_json['image_pixel_width'])
        self.setParam('n_modules', config_json['n_modules'])
        self.setParam('start_udp_port', config_json['start_udp_port'])
