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
    def __init__(self, url_base):
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
        return self._get_url(WRITER_STATUS_ENDPOINT)

    def get_stats(self):
        return self._get_url(DAQ_STATS_ENDPOINT)['stats']

    def get_logs(self, n_last_logs):
        r = requests.get(self.url_base + DAQ_LOGS_ENDPOINT.split('<')[0] + str(n_last_logs))
        return self._get_json_from_response(r)['logs']

    def get_deployment_status(self):
        return self._get_url(DAQ_DEPLOYMENT_STATUS_ENDPOINT)['deployment']
