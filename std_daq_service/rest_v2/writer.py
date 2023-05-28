import logging
from threading import Event, Thread
from time import time, sleep, time_ns

import zmq
from zmq import Again

from std_daq_service.rest_v2.redis_storage import StdDaqRedisStorage
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


# The updates should be coming at 1 Hz anyway.
RECV_TIMEOUT = 500


class StatusLogger(object):
    def __init__(self, ctx, storage: StdDaqRedisStorage, writer_status_url):
        self.ctx = ctx
        self.storage = storage
        self.writer_status_url = writer_status_url

        self.stop_event = Event()
        self.processing_thread = Thread(target=self._processing)
        self.processing_thread.start()

    def _processing(self):
        receiver = self.ctx.socket(zmq.SUB)
        receiver.connect(self.writer_status_url)
        receiver.setsockopt_string(zmq.SUBSCRIBE, "")
        receiver.setsockopt(zmq.RCVTIMEO, RECV_TIMEOUT)

        _logger.info("Starting status logger.")

        while not self.stop_event.is_set():
            try:
                status = receiver.recv_json()
                daq_status = status['writer']
                self.storage.add_writer_status(writer_status=daq_status)
            except Again:
                pass
            except Exception:
                _logger.exception("Error in status logger.")

        _logger.info("Stopping status logger.")

    def close(self):
        self.stop_event.set()
        self.processing_thread.join()
