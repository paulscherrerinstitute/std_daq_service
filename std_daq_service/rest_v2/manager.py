import logging
from utils import update_config

_logger = logging.getLogger("StartStopRestManager")


class StartStopRestManager(object):
    def __init__(self, ctx, writer_driver, config_driver):
        self.writer_driver = writer_driver
        self.config_driver = config_driver

    def write_sync(self, output_file, n_images):
        writer_status = self.writer_driver.get_state()
        if writer_status['state'] != "READY":
            raise RuntimeError('Cannot start writing until writer state is READY. '
                               'Stop the current acquisition or wait for it to finish.')

        return self.get_status()

    def write_async(self, output_file, n_images):
        state = self.writer_driver.get_state()
        if state['state'] != "READY":
            raise RuntimeError('Cannot start writing until writer state is READY. '
                               'Stop the current acquisition or wait for it to finish.')

        return self.get_status()

    def stop_writing(self):
        return self.get_status()

    def get_status(self):
        return self.writer_driver.get_status()

    def get_config(self):
        return self.config_driver.get_config()

    def set_config(self, config_updates):
        new_config = update_config(self.get_config(), config_updates)
        self.config_driver.deploy_config(new_config)

        return new_config

    def close(self):
        _logger.info("Shutting down manager.")
        self.writer_driver.close()