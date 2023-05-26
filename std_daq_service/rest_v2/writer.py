import logging
from time import time, sleep, time_ns

from std_daq_service.writer_driver.start_stop_driver import WriterDriver

_logger = logging.getLogger("WriterRestManager")

# How much time to sleep between checks on the status, in seconds.
SYNC_SLEEP_INTERVAL = 0.1
# How many seconds should the sync request last - at most.
SYNC_WAIT_TIMEOUT = 60


class WriterRestManager(object):
    def __init__(self, writer_driver: WriterDriver):
        self.writer_driver = writer_driver

    def write_sync(self, output_file, n_images, run_id):
        self.writer_driver.start({
            'run_id': run_id,
            'output_file': output_file,
            'n_images': n_images
        })

        start_time = time()
        while True:
            status = self.get_status()
            if status != 'WRITING':
                return status

            sleep(SYNC_SLEEP_INTERVAL)

            if time() - start_time > SYNC_WAIT_TIMEOUT:
                raise RuntimeError(f"Your acquisition is still running, just the REST call has ended. "
                                   f"Sync acquisition limit of {SYNC_WAIT_TIMEOUT} seconds exceeded. "
                                   f"Use async write call for long acquisitions.")

    def write_async(self, output_file, n_images, user_id):
        self.writer_driver.start({
            'run_id': user_id,
            'output_file': output_file,
            'n_images': n_images
        })

        return self.get_status()

    def stop_writing(self):
        self.writer_driver.stop()
        return self.get_status()

    def get_status(self):
        return self.writer_driver.get_status()

    def close(self):
        _logger.info("Shutting down writer manager.")
        self.writer_driver.close()
