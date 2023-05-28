import logging

from std_daq_service.rest_v2.utils import update_config


_logger = logging.getLogger("DaqRestManager")
# milliseconds
RECV_TIMEOUT = 100


class DaqRestManager(object):
    def __init__(self, storage):
        self.storage = storage

    def get_config(self):
        return self.storage.get_config()

    def set_config(self, config_updates):
        config_id, daq_config = self.storage.get_config()
        new_daq_config = update_config(daq_config, config_updates)

        _logger.info(f"Set new daq_config {new_daq_config}")
        self.storage.set_config(new_daq_config)
        return new_daq_config

    def get_stats(self):
        return self.storage.get_stat()

    def get_logs(self, n_logs):
        return self.storage.get_logs(n_logs)

    def get_deployment_status(self):
        return self.storage.get_deployment_status()


