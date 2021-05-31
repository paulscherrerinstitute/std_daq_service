
class StatusAggregator(object):
    def __init__(self, on_status_change_function):
        self.on_status_change = on_status_change_function
        self.status = {}

    def on_broker_message(self, request_id, header, request):
        if request_id not in self.status:
            self.status[request_id] = {'request': request,
                                       'services': {}}

        service_name = header['source']

        if service_name not in self.status[request_id]['services']:
            self.status[request_id]['services'][service_name] = []

        self.status[request_id]['services'][service_name].append((header['action'], header['message']))

        self.on_status_change(request_id, self.status[request_id])

    def wait_for_response(self, request_id):
        pass
