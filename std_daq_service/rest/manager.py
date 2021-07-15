from std_daq_service.broker.client import BrokerClient
from std_daq_service.broker.status_aggregator import StatusAggregator


class RestManager(object):
    def __init__(self, broker_url, tag):
        self.status_aggregator = StatusAggregator()
        self.broker_client = BrokerClient(broker_url, tag,
                                          status_callback=self.status_aggregator.on_status_message)

    def write_sync(self, message):
        request_id = self.broker_client.send_request(message)
        broker_response = self.status_aggregator.wait_for_complete(request_id)
        return request_id, broker_response

    def write_async(self, message):
        return self.broker_client.send_request(message)

    def kill_sync(self, request_id):
        self.broker_client.kill_request(request_id)
        broker_response = self.status_aggregator.wait_for_complete(request_id)

        return broker_response
