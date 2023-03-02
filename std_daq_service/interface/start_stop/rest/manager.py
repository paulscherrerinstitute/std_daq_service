import logging

_logger = logging.getLogger("StartStopRestManager")

class StartStopRestManager(object):
    def __init__(self, ctx, writer_driver, config_driver):
        self.writer_driver = writer_driver
        self.config_driver = config_driver

    def write_sync(self, output_file, n_images):
        if self.writer_state['state'] != "READY":
            raise RuntimeError('Cannot start writing until writer state is READY. '
                               'Stop the current acquisition or wait for it to finish.')

        return self.get_status()

    def write_async(self, output_file, n_images):
        if self.writer_state['state'] != "READY":
            raise RuntimeError('Cannot start writing until writer state is READY. '
                               'Stop the current acquisition or wait for it to finish.')

        return self.get_status()

    def stop_writing(self):
        return self.get_status()

    def get_status(self):
        return self.writer_state

    def get_config(self):
        return None

    def set_config(self, config_updates):
        return self.get_config()

    def close(self):
        _logger.info("Shutting down manager.")
        self.driver.close()