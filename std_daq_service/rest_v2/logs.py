from threading import Event, Thread

import zmq
from zmq import Again

from std_daq_service.rest_v2.daq import RECV_TIMEOUT, _logger


class LogsLogger(object):
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
                    self.storage.add_log(acq_status)
            except Again:
                pass

        _logger.info("Stopping acquisition logger.")

    def close(self):
        self.stop_event.set()
        self.processing_thread.join()
