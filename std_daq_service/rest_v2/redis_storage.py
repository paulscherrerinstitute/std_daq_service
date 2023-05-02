import json
import logging

_logger = logging.getLogger("StdDaqRedisStorage")

FIELD_DAQ_CONFIG_JSON = b'json'


class StdDaqRedisStorage(object):
    def __init__(self, redis, redis_namespace):
        _logger.info(f"Using namespace {redis_namespace}.")
        self.redis = redis

        self.KEY_CONFIG = f'{redis_namespace}:config'

    def get_config(self):
        response = self.redis.xrevrange(self.KEY_CONFIG, count=1)
        # Fails before a beamline is configured for the first time.
        if len(response) > 0:
            config_id = response[0][0].decode('utf8')
            daq_config = json.loads(response[0][1][FIELD_DAQ_CONFIG_JSON])
            return config_id, daq_config
        else:
            return None, None

    def set_config(self, daq_config):
        _logger.info(f"Set config {daq_config} to key {self.KEY_CONFIG}")
        config_id = self.redis.xadd(self.KEY_CONFIG, {FIELD_DAQ_CONFIG_JSON: json.dumps(daq_config)}).encode('uint8')
        _logger.info(f"Config got config_id {config_id}")

    @staticmethod
    def _interpret_deployment_status(deployed_servers):
        if len(deployed_servers) == 0:
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

    def get_deployment_status(self):
        config_id, _ = self.get_config()

        deployed_servers = {}
        start_timestamp = 0
        stop_timestamp = 0

        if config_id is not None:
            start_timestamp = self._redis_to_unix_timestamp(config_id)

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
                'servers': deployed_servers,
                'stats': {'start_time': start_timestamp, 'stop_time': stop_timestamp}}

    def set_deployment_status(self, config_id, server_name, message):
        _logger.info(f"Set deployment status on config_id {config_id} from "
                     f"server_name {server_name} with message {message}.")

        deployment_status_id = self.redis.xadd(
            self._get_deployment_key(config_id), {
                'server_name': server_name,
                'message': message
            }).encode('utf8')

        return deployment_status_id
