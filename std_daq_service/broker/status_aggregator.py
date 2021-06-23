from collections import deque

MAX_REQUEST_ID_CACHE = 100


class StatusAggregator(object):
    def __init__(self, status_change_callback=None):
        self.status_change_callback = status_change_callback
        self.status = {}

        self.cache_length = MAX_REQUEST_ID_CACHE
        self.request_id_buffer = deque(maxlen=self.cache_length)

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
