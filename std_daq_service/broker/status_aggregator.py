from collections import deque
from time import time

import zmq

from std_daq_service.broker.common import ACTION_REQUEST_SUCCESS, ACTION_REQUEST_FAIL

MAX_REQUEST_ID_CACHE = 100


class StatusAggregator(object):
    def __init__(self, status_change_callback=None):
        self.status_change_callback = status_change_callback
        self.status = {}

        self.cache_length = MAX_REQUEST_ID_CACHE
        self.request_id_buffer = deque(maxlen=self.cache_length)

        self.ctx = zmq.Context()
        self.sender = self.ctx.socket(zmq.PUB)
        self.sender.bind("inproc://status_change")

    def on_status_message(self, request_id, request, header):
        if request_id not in self.status:
            # Allow a max of MAX_REQUEST_ID_CACHE entries in the cache.
            if len(self.request_id_buffer) == self.cache_length:
                del self.status[self.request_id_buffer[0]]

            self.request_id_buffer.append(request_id)
            self.status[request_id] = {'request': request,
                                       'services': {}}

        service_name = header['source']

        if service_name not in self.status[request_id]['services']:
            self.status[request_id]['services'][service_name] = []

        self.status[request_id]['services'][service_name].append((header['action'], header['message']))

        if self.status_change_callback is not None:
            self.status_change_callback(request_id, self.status[request_id])

        self.sender.send_json({'request_id': request_id,
                               'status': self.status[request_id]})

    def wait_for_complete(self, request_id, timeout=10):
        receiver = self.ctx.socket(zmq.SUB)
        receiver.setsockopt(zmq.RCVTIMEO, 200)
        receiver.setsockopt_string(zmq.SUBSCRIBE, '')
        receiver.connect("inproc://status_change")

        start_time = time()
        while time() - start_time < timeout:
            try:
                status_update = receiver.recv_json()
            except zmq.Again:
                continue

            if status_update['request_id'] != request_id:
                continue

            for service_name, statuses in sorted(status_update['status']['services'].items()):
                last_received_status = statuses[-1][0]

                if last_received_status not in (ACTION_REQUEST_SUCCESS, ACTION_REQUEST_FAIL):
                    break
            else:
                receiver.close()
                return {'status': last_received_status,
                        'request_details': status_update['status']['request']}

        else:
            receiver.close()
            raise TimeoutError("The request did not complete in time.")
