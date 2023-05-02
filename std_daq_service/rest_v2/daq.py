import json
import logging
import time

from redis.client import Redis

from std_daq_service.rest_v2.redis import StdDaqRedisStorage
from std_daq_service.rest_v2.stats import ImageMetadataStatsDriver
from std_daq_service.rest_v2.utils import update_config
from std_daq_service.writer_driver.start_stop_driver import WriterDriver


_logger = logging.getLogger("DaqRestManager")


class DaqRestManager(object):
    def __init__(self, config_file, stats_driver: ImageMetadataStatsDriver, writer_driver: WriterDriver, redis: Redis):
        self.stats_driver = stats_driver
        self.writer_driver = writer_driver

        self.storage = StdDaqRedisStorage(redis=redis, redis_namespace=config_file)

    def get_config(self):
        return self.storage.get_config()

    def set_config(self, config_updates):
        config_id, daq_config = self.storage.get_config()
        new_daq_config = update_config(daq_config, config_updates)

        _logger.info(f"Set new daq_config {new_daq_config}")
        self.storage.set_config(new_daq_config)
        return new_daq_config

    def get_stats(self):
        return self.stats_driver.get_stats()

    def get_logs(self, n_logs):
        return self.writer_driver.get_logs(n_logs)

    def get_deployment_status(self):
        return self.storage.get_deployment_status()

    def close(self):
        self.stats_driver.close()
