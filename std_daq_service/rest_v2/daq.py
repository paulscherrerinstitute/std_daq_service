import logging
from threading import Event, Thread

import zmq
from zmq import Again

from std_daq_service.rest_v2.stats import StatsDriver
from std_daq_service.rest_v2.utils import update_config
from std_daq_service.writer_driver.start_stop_driver import WriterDriver


_logger = logging.getLogger("DaqRestManager")
# milliseconds
RECV_TIMEOUT = 100


class DaqRestManager(object):
    def __init__(self, config_file, stats_driver: StatsDriver, writer_driver: WriterDriver, storage):
        self.stats_driver = stats_driver
        self.writer_driver = writer_driver
        self.writer_acq_logger = WriterAcquisitionLogger(zmq.Context(), writer_driver.out_status_address, storage)

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
        return self.stats_driver.get_stats()

    def get_logs(self, n_logs):
        return self.storage.get_acquisition_logs(n_logs)

    def get_deployment_status(self):
        return self.storage.get_deployment_status()

    def close(self):
        self.stats_driver.close()
        self.writer_acq_logger.close()


class WriterAcquisitionLogger(object):
    def __init__(self, ctx, status_address, storage):
        self.ctx = ctx
        self.status_address = status_address
        self.storage = storage

        self.stop_event = Event()
        self.processing_thread = Thread(target=self._processing)
        self.processing_thread.start()

    def _processing(self):
        receiver = self.ctx.socket(zmq.SUB)
        receiver.connect(self.status_address)
        receiver.setsockopt_string(zmq.SUBSCRIBE, "")
        receiver.setsockopt(zmq.RCVTIMEO, RECV_TIMEOUT)

        _logger.info("Starting acquisition logger.")

        while not self.stop_event.is_set():
            try:
                status = receiver.recv_json()
                acq_status = status['acquisition']
                if acq_status['state'] == 'FINISHED' and acq_status['stats']['start_time'] is not None:
                    self.storage.add_acquisition_log(acq_status)
            except Again:
                pass

        _logger.info("Stopping acquisition logger.")

    def close(self):
        self.stop_event.set()
        self.processing_thread.join()
