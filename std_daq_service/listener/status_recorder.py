from collections import deque

MAX_REQUEST_ID_CACHE = 100


class StatusRecorder(object):
    def __init__(self, on_status_change_function):
        self.on_status_change = on_status_change_function
        self.status = {}

        self.cache_length = MAX_REQUEST_ID_CACHE
        self.request_id_buffer = deque(maxlen=self.cache_length)

    def on_status_message(self, request_id, header, request):
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

        self.on_status_change(request_id, self.status[request_id])
