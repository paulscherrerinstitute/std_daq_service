
class StatusAggregator(object):
    def __init__(self):
        self.status = {}

    def on_broker_message(self, request_id, header, request):
        if request_id not in self.status:
            self.status[request_id] = {'request': request,
                                       'services': {}}

        service_name = header['source']

        if service_name not in self.status[request_id]['services']:
            self.status[request_id]['services'][service_name] = []

        self.status[request_id]['services'][service_name].append((header['action'], header['message']))
        # TODO: Somehow know when the request is finished, then signal.

    def wait_for_response(self, request_id):
        # TODO: Implement async communication and wait until a status OK has arrived for the requested request_id.
        pass
