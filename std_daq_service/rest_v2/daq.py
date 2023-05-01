import json
import logging
import time

from redis.client import Redis

from std_daq_service.rest_v2.stats import ImageMetadataStatsDriver
from std_daq_service.rest_v2.utils import update_config
from std_daq_service.writer_driver.start_stop_driver import WriterDriver


_logger = logging.getLogger("DaqRestManager")


def redis_to_unix_timestamp(redis_id):
    return float(redis_id.replace('-', '.')) / 1000


class DaqRestManager(object):
    def __init__(self, config_file, stats_driver: ImageMetadataStatsDriver, writer_driver: WriterDriver, redis: Redis):
        self.stats_driver = stats_driver
        self.writer_driver = writer_driver

        self.redis = redis
        self.config_key = f'{config_file}:config'
        self.config_status_key = f'{config_file}:config_status'

    def get_config(self):
        messages = self.redis.xrevrange(self.config_key)
        if len(messages) > 0:
            config_id = messages[0][0].decode('utf8')
            daq_config = json.loads(messages[0][1][b'daq_config'])
            return config_id, daq_config
        else:
            return "", {}

    def set_config(self, config_updates):
        config_id, daq_config = self.get_config()
        new_daq_config = update_config(daq_config, config_updates)
        self.redis.xadd(self.config_key, {b'daq_config': json.dumps(new_daq_config)})
        return new_daq_config

    def get_stats(self):
        return self.stats_driver.get_stats()

    def get_logs(self, n_logs):
        return self.writer_driver.get_logs(n_logs)

    def get_deployment_status(self):
        messages = self.redis.xrevrange(self.config_key)

        daq_config_id = None
        deployed_servers = {}
        start_timestamp = 0
        stop_timestamp = 0

        status = 'UNKNOWN'
        message = "No deployment records."

        if len(messages) > 0:
            daq_config_id = messages[0][0].decode()
            start_timestamp = redis_to_unix_timestamp(daq_config_id)
            statuses = self.redis.xrange(self.config_status_key, min=daq_config_id)

            # Collect latest status from each server.
            for status in statuses:
                daq_config = status[1]
                status_config_id = daq_config[b'config_id'].decode()
                stop_timestamp = max(stop_timestamp, redis_to_unix_timestamp(status_config_id))

                if daq_config_id == status_config_id:
                    server_name = daq_config[b'server_name'].decode()
                    server_message = daq_config[b'message'].decode()
                    # Return only the last message received from a specific server.
                    deployed_servers[server_name] = server_message
                else:
                    break
            if len(deployed_servers) == 0:
                status = 'RUNNING'
                message = 'Waiting for servers...'
            if all(message == 'Done' for message in deployed_servers.values()):
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

        return {'config_id': daq_config_id,
                'status': status,
                'message': message,
                'servers': deployed_servers,
                'stats': {'start_time': start_timestamp, 'stop_time': stop_timestamp}}

    def close(self):
        self.stats_driver.close()
