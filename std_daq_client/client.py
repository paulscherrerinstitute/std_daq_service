import requests

STATUS_ENDPOINT = '/status'
START_ENDPOINT = '/start'
STOP_ENDPOINT = '/stop'

WRITER_WRITE_SYNC_ENDPOINT = "/writer/write_sync"
WRITER_WRITE_ASYNC_ENDPOINT = "/writer/write_async"
WRITER_STATUS_ENDPOINT = "/writer/status"
WRITER_STOP_ENDPOINT = "/writer/stop"

SIM_STATUS_ENDPOINT = '/simulation' + STATUS_ENDPOINT
SIM_START_ENDPOINT = '/simulation' + START_ENDPOINT
SIM_STOP_ENDPOINT = '/simulation' + STOP_ENDPOINT

DAQ_LIVE_STREAM_ENDPOINT = '/daq/live'
DAQ_CONFIG_ENDPOINT = '/daq/config'
DAQ_STATS_ENDPOINT = '/daq/stats'
DAQ_LOGS_ENDPOINT = '/daq/logs/<int:n_logs>'
DAQ_DEPLOYMENT_STATUS_ENDPOINT = '/daq/deployment'


class StdDaqAdminException(Exception):
    pass


class StdDaqClient(object):
    def __init__(self, url_base='http://localhost:5000'):
        """
        REST client for the standard-daq admin interface.

        :param url_base: URL on which the admin interface is running. Usually port 5000.
        """
        self.url_base = url_base

    @staticmethod
    def _get_json_from_response(r):
        if r.status_code != 200:
            raise RuntimeError(r.raw)

        response = r.json()
        if response['status'] != "ok":
            raise StdDaqAdminException(response['message'])

        return response

    def _post_url(self, url_postfix, json_payload):
        return self._get_json_from_response(requests.post(self.url_base + url_postfix, json=json_payload))

    def _get_url(self, url_postfix):
        return self._get_json_from_response(requests.get(self.url_base + url_postfix))

    def get_config(self):
        """
        Retrieves the current DAQ configuration.

        Return dictionary format:
        {
          "bit_depth": 16,                   # Bit depth of the image. Supported values are dependent on the detector.
          "detector_name": "EG9M",           # Name of the detector. Must be unique, used as internal DAQ identifier.
          "detector_type": "eiger",          # Type of detector. Currently supported: eiger, jungfrau, gigafrost.
          "image_pixel_height": 3264,        # Assembled image height in pixels.
          "image_pixel_width": 3106,         # Assembled image width in pixels.
          "n_modules: 2,                     # Number of modules to assemble.
          "start_udp_port": 50000,           # Start UDP port where the detector is streaming modules.
          "module_positions": {              # Dictionary with mapping between module number -> image possition.
            "0": [0, 3263, 513, 3008 ],      #     Format: [start_x, start_y, end_x, end_y]
            "1": [516, 3263, 1029, 3008 ],
        }

        :return: Dictionary with current configuration.
        """
        return self._get_url(DAQ_CONFIG_ENDPOINT)['config']

    def set_config(self, daq_config):
        return self._post_url(DAQ_CONFIG_ENDPOINT, daq_config)['config']

    def start_writer_async(self, write_request):
        return self._post_url(WRITER_WRITE_ASYNC_ENDPOINT, write_request)

    def start_writer_sync(self, write_request):
        return self._post_url(WRITER_WRITE_SYNC_ENDPOINT, write_request)

    def stop_writer(self):
        return self._post_url(WRITER_STOP_ENDPOINT, {})

    def get_status(self):
        """
        Return the current DAQ status.

        Return dictionary format:
        {
          "acquisition": {                        # Stats about the currently running or last finished acquisition.
            "info": {                             #    Acquisition request
              "n_images": 100,                    #        Number of images
              "output_file": "/tmp/test.h5",      #        Output file
              "run_id": 1684930336122153839       #
            },
            "message": "Completed.",
            "state": "FINISHED",
            "stats": {
              "n_write_completed": 100,
              "n_write_requested": 100,
              "start_time": 1684930336.1252322,
              "stop_time": 1684930345.2723851
            }
          },
          "state": "READY"                        # State of the writer: READY (to write), WRITING
        }


        :return: Dictionary with current status.
        """
        return self._get_url(WRITER_STATUS_ENDPOINT)['writer']

    def get_stats(self):
        return self._get_url(DAQ_STATS_ENDPOINT)['stats']

    def get_logs(self, n_last_logs):
        r = requests.get(self.url_base + DAQ_LOGS_ENDPOINT.split('<')[0] + str(n_last_logs))
        return self._get_json_from_response(r)['logs']

    def get_deployment_status(self):
        return self._get_url(DAQ_DEPLOYMENT_STATUS_ENDPOINT)['deployment']
