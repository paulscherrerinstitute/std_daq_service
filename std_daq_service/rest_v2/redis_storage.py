import json
import logging
from collections import OrderedDict

_logger = logging.getLogger("StdDaqRedisStorage")

FIELD_DAQ_JSON = b'json'


class StdDaqRedisStorage(object):
    def __init__(self, redis, redis_namespace='daq'):
        _logger.info(f"Using namespace {redis_namespace}.")
        self.redis = redis

        if not self.redis.ping():
            raise RuntimeError("Cannot connect to object store. Is Redis running?")

        self.KEY_CONFIG = f'{redis_namespace}:config'
        self.KEY_LOG = f'{redis_namespace}:log'
        self.KEY_STAT = f'{redis_namespace}:stat'
        self.KEY_STATUS = f'{redis_namespace}:status'

    def get_config(self):
        response = self.redis.xrevrange(self.KEY_CONFIG, count=1)
        # Fails before a beamline is configured for the first time.
        if response:
            config_id = response[0][0].decode('utf8')
            daq_config = json.loads(response[0][1][FIELD_DAQ_JSON])
            return config_id, daq_config
        else:
            return None, None

    def set_config(self, daq_config):
        _logger.info(f"Set config {daq_config} to key {self.KEY_CONFIG}")
        config_id = self.redis.xadd(self.KEY_CONFIG, {FIELD_DAQ_JSON: json.dumps(daq_config)}).decode('utf8')
        _logger.info(f"Config got config_id {config_id}")

    @staticmethod
    def _interpret_deployment_status(deployed_servers):
        if deployed_servers is None:
            status = 'UNKNOWN'
            message = 'No config available'
        elif len(deployed_servers) == 0:
            status = 'UNKNOWN'
            message = 'Waiting for servers...'
        elif all(message == 'Done' for message in deployed_servers.values()):
            status = 'SUCCESS'
            message = 'Deployment successful'
        elif any(message == 'Error' for message in deployed_servers.values()):
            status = 'ERROR'
            message = "Deployment failed"
        elif any(message == 'Deploying' for message in deployed_servers.values()):
            status = 'RUNNING'
            message = 'Deploying on servers...'
        else:
            status = 'UNKNOWN'
            message = 'Unexpected state. Check logs on Elastic.'
            _logger.warning(f"Unexpected deployment status: {deployed_servers}")

        return status, message

    @staticmethod
    def _redis_to_unix_timestamp(redis_timestamp):
        return float(redis_timestamp.replace('-', '.')) / 1000

    def _get_deployment_key(self, config_id):
        return f'{self.KEY_CONFIG}:{config_id}'

    def _get_report_key(self, log_id):
        return f'{self.KEY_LOG}:{log_id}'

    def get_deployment_status(self):
        config_id, _ = self.get_config()

        deployed_servers = None
        start_timestamp = 0
        stop_timestamp = 0

        if config_id is not None:
            start_timestamp = self._redis_to_unix_timestamp(config_id)
            deployed_servers = {}
            # Collect latest status from each server.
            for deployment_event in self.redis.xrange(self._get_deployment_key(config_id)):
                deployment_event_id = deployment_event[0].decode('utf8')
                stop_timestamp = max(stop_timestamp, self._redis_to_unix_timestamp(deployment_event_id))

                deployment_status = deployment_event[1]

                server_name = deployment_status[b'server_name'].decode()
                server_message = deployment_status[b'message'].decode()

                # Return only the last state received from a specific server.
                deployed_servers[server_name] = server_message

        status, message = self._interpret_deployment_status(deployed_servers)

        return {'config_id': config_id,
                'status': status,
                'message': message,
                'servers': deployed_servers or {},
                'stats': {'start_time': start_timestamp, 'stop_time': stop_timestamp}}

    def set_deployment_status(self, config_id, server_name, message):
        _logger.info(f"Set deployment status on config_id {config_id} from "
                     f"server_name {server_name} with message {message}.")

        deployment_status_id = self.redis.xadd(
            self._get_deployment_key(config_id), {
                'server_name': server_name,
                'message': message
            }).decode('utf8')

        return deployment_status_id

    def add_log(self, acq_status):
        _logger.info(f"Adding finished acquisition {acq_status} to log.")
        self.redis.xadd(self.KEY_LOG, {FIELD_DAQ_JSON: json.dumps(acq_status)})

    def get_logs(self, n_acquisitions):
        logs_bytes = self.redis.xrevrange(self.KEY_LOG, count=n_acquisitions)
        logs_dict = OrderedDict()
        for log_id, log_data in logs_bytes:
            logs_dict[log_id] = json.loads(log_data[FIELD_DAQ_JSON])

        return logs_dict

    def add_writer_status(self, writer_status):
        self.redis.xadd(self.KEY_STATUS, {FIELD_DAQ_JSON: json.dumps(writer_status)})

    def add_stat(self, stat):
        self.redis.xadd(self.KEY_STAT, {FIELD_DAQ_JSON: json.dumps(stat)})

    def get_stat(self):
        response = self.redis.xrevrange(self.KEY_STAT, count=1)
        # Fails before a beamline is configured for the first time.
        if response:
            stat = json.loads(response[0][1][FIELD_DAQ_JSON])
            return stat
        else:
            return None

    def add_report(self, log_id, report):
        _logger.info(f"Adding validation report to log {log_id}.")
        self.redis.xadd(self._get_report_key(log_id), {FIELD_DAQ_JSON: json.dumps(report)})
        pass

    def get_reports(self, log_id):
        reports_bytes = self.redis.xrange(self._get_report_key(log_id))
        reports = [json.loads(x[1][FIELD_DAQ_JSON]) for x in reports_bytes]
        return reports
