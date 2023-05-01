import json
import logging

from redis.client import Redis

from std_daq_service.rest_v2.stats import ImageMetadataStatsDriver
from std_daq_service.rest_v2.utils import update_config
from std_daq_service.writer_driver.start_stop_driver import WriterDriver


_logger = logging.getLogger("DaqRestManager")


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

        if len(messages) > 0:
            daq_config_id = messages[0][0]
            statuses = self.redis.xrange(self.config_status_key, min=daq_config_id)

            deployed_servers = []
            for status in statuses:
                status_config_id = status[0]
                if daq_config_id == status_config_id:
                    status_config_server = status[1][b'server_name'].decode('utf8')
                    deployed_servers.append(status_config_server)

            return {'config_id': daq_config_id,
                    'servers': deployed_servers}

    def close(self):
        self.stats_driver.close()
