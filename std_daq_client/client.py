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
          "detector_type": "eiger",          # Type of detector. Currently supported: eiger, jungfrau, gigafrost, bsread
          "image_pixel_height": 3264,        # Assembled image height in pixels.
          "image_pixel_width": 3106,         # Assembled image width in pixels.
          "n_modules: 2,                     # Number of modules to assemble.
          "start_udp_port": 50000,           # Start UDP port where the detector is streaming modules.
          "writer_user_id": 12345,           # User_id under which the writer will create and write the file.
          "module_positions": {              # Dictionary with mapping between module number -> image position.
            "0": [0, 3263, 513, 3008 ],      #     Format: [start_x, start_y, end_x, end_y]
            "1": [516, 3263, 1029, 3008 ],
        }

        :return: Dictionary with current configuration.
        """
        return self._get_url(DAQ_CONFIG_ENDPOINT)['config']

    def set_config(self, daq_config):
        """
        Set the config of the DAQ. This will cause the system to restart. It takes about 10 seconds for everything
        to stabilize after applying the config. Running the detector for 10 seconds after each config change is
        strongly suggested to verify the automatic tuning done its job correctly.

        You can pass the entire config JSON or just the difference you want applied. The exception is module_positions:
        always specify all modules you want to use, but if you don't want to change the module_positions just omit this
        property from your daq_config you pass to this function.

        In the most common case, changing 'writer_user_id' and 'bit_depth', the daq_config would look like:
        {
          'writer_user_id': 0,
          'bit_depth': 16
        }

        NOTE: A 'writer_user_id' that is < 1 means 'Use the user the service was started with'. In general, you should
        provide the e-account user_id for the experiment and using the service account only for debugging.
        (the user_id is the username without the initial 'e', for example e-account 'e12345' has a user_id of 12345).

        :param daq_config: Dictionary with config fields you want to change.
        :return: Dictionary with the config that was applied.
        """
        return self._post_url(DAQ_CONFIG_ENDPOINT, daq_config)['config']

    def start_writer_async(self, write_request):
        """
        Start writing and return immediately. The 'async' here refers to the fact that the call will NOT block until
        the writing is finished.

        Example write_request:
        {
          "n_images":100,                   # Number of images to collect.
          "run_id":"20230526_113713.793",   # Run_id. Can be anything, but it should be unique. Timestamp usually.
          "output_file":"/tmp/eiger.h5"     # Output filename. Absolute path only.
        }

        If you do not provide a run_id, it will be set automatically to the current timestamp.

        :param write_request: Dictionary with the required keys.
        :return: Dictionary with the DAQ status.
        """
        return self._post_url(WRITER_WRITE_ASYNC_ENDPOINT, write_request)['writer']

    def start_writer_sync(self, write_request):
        """
        Start writing and return when finished. The 'sync' here refers to the fact that the call will block until
        the writing is finished.

        Example write_request:
        {
          "n_images":100,                   # Number of images to collect.
          "run_id":"20230526_113713.793",   # Run_id. Can be anything, but it should be unique. Timestamp usually.
          "output_file":"/tmp/eiger.h5"     # Output filename. Absolute path only.
        }

        If you do not provide a run_id, it will be set automatically to the current timestamp.

        :param write_request: Dictionary with the required keys.
        :return: Dictionary with the DAQ status.
        """
        return self._post_url(WRITER_WRITE_SYNC_ENDPOINT, write_request)['writer']

    def stop_writer(self):
        """
        Stop the writing immediately.
        Also used to reset the driver in case the writer crushed and restarted in the background.

        When the writer process dies due to an error, it gets restarted after a couple of seconds. The driver might
        recover from this event, but it might also not be able to. This is the case when the status of the writer
        is 'UNKNOWN'. When this happens call the 'stop_writer' function to re-establish the connection between the
        driver and the writer.
        """
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
              "run_id": 1684930336122153839       #        Run_id (start timestamp)
            },
            "message": "Completed.",              # User displayable message from the writer.
            "state": "FINISHED",                  # State of the acquisition.
            "stats": {                            # Stats of the acquisition.
              "n_write_completed": 100,           #     Number of completed writes
              "n_write_requested": 100,           #     Number of requested writers from the driver
              "start_time": 1684930336.1252322,   #     Acquisition start timestamp
              "stop_time": 1684930345.2723851     #     Acquisition stop timestamp
            }
          },
          "state": "READY"                        # State of the writer: READY (to write), WRITING
        }

        :return: Dictionary with current status.
        """
        return self._get_url(WRITER_STATUS_ENDPOINT)['writer']

    def get_stats(self):
        """
        Returns the current DAQ statistics in terms of detector and writer throughput.
        This statistics is aggregated for each second. You can use this numbers to roughly diagnose if the
        system is having performance issues. The numbers are from the DAQ perspective (what the DAQ 'sees').

        Example return object:
        {
          "detector": {                 # Detector statistics
            "bytes_per_second": 0.0,    #   Throughput
            "images_per_second": 0.0    #   Frequency
          },
          "writer": {                   # Writer statistics
            "bytes_per_second": 0.0,    #   Throughput
            "images_per_second": 0.0    #   Frequency
          }
        }

        :return: Dictionary with DAQ statistics.
        """
        return self._get_url(DAQ_STATS_ENDPOINT)['stats']

    def get_logs(self, n_last_logs):
        """
        Return the list of the last N acquisitions that produced a file.
        If the acquisition failed to finish for whatever reason there will be no record of it.

        Example reply with a single acquisition:
        [
          {
            "info": {                            # Write request for this acquisition
              "n_images": 10000,                 #   Number of requested images
              "output_file": "/tmp/delme.h5",    #   Output file name.
              "run_id": 1685021686383453199      #   run_id (timestamp of the request time)
            },
            "message": "Interrupted.",           # User readable state with which the acquisition finished.
            "state": "FINISHED",                 # Current state of the acquisition. Check docs for details.
            "stats": {                           # Statistics regarding this acquisition
              "n_write_completed": 7354,         #   Number of images on disk
              "n_write_requested": 7354,         #   Number of write requested to the writer
              "start_time": 1685021686.3889894,  #   Start timestamp of the writing.
              "stop_time": 1685021732.6660495    #   Stop timestamp of the writing.
            }
          }
        ]

        The reply is always a list of acquisition records (an empty list in case there are no records).

        :param n_last_logs: Number of records to return.
        :return: List of acquisition records.
        """
        r = requests.get(self.url_base + DAQ_LOGS_ENDPOINT.split('<')[0] + str(n_last_logs))
        return self._get_json_from_response(r)['logs']

    def get_deployment_status(self):
        """
        Return the status of the last deployment request.
        This is useful to check if your last config file was picked up by all servers.

        Example response:
        {
          "config_id": "1685090990182-0",       # Configuration id -> timestamp of the config change.
          "message": "Deployment successful",   # User displayable message
          "servers": {                          # Dictionary of server that replied to the config change.
            "xbl-daq-28": "Done"                #   server_name : status
            "xbl-daq-29": "Done"                #
          },
          "stats": {                            # Statistics regarding the deployment
            "start_time": 1685090990.182,       #   Start time of the deployment
            "stop_time": 1685090990.347         #   End time of the deployment
          },
          "status": "SUCCESS"                   # Current status of the deployment.
        }

        When the deployment is finished the DAQ is actually not yet ready to operate. The deployment itself takes only
        milliseconds while the process restart and stabilization procedure takes seconds. A good estimate would be 10
        seconds for the system to stabilize again. During the stabilization time, running the detector helps.

        :return: Dictionary with the last deployment state.
        """
        return self._get_url(DAQ_DEPLOYMENT_STATUS_ENDPOINT)['deployment']
