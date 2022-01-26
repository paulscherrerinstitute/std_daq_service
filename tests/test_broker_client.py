import unittest
from time import sleep

from std_daq_service.broker.client import BrokerClient
from std_daq_service.broker.common import TEST_BROKER_URL, ACTION_REQUEST_START, ACTION_REQUEST_SUCCESS
from std_daq_service.broker.primary_service import PrimaryBrokerService

# TODO: Fix resource warning when closing Pika.


class TestBrokerListener(unittest.TestCase):
    def test_broker_listener_workflow(self):
        service_name = "noop_worker"

        sent_request = {
            "this is a": 'request'
        }
        service_message = "IT WORKS!!"

        status_messages = []
        sent_request_id = None

        def status_callback(request_id, request, header):
            self.assertEqual(request_id, sent_request_id)
            self.assertEqual(header["source"], service_name)

            status_messages.append((request_id, header, request))

        def request_callback(request_id, request):
            self.assertEqual(request_id, sent_request_id)
            self.assertEqual(sent_request, request)
            return service_message

        client = BrokerClient(broker_url=TEST_BROKER_URL, tag="beamline.*",
                              status_callback=status_callback)

        worker = PrimaryBrokerService(broker_url=TEST_BROKER_URL,
                                      service_name=service_name,
                                      request_callback=request_callback)

        sleep(0.1)
        sent_request_id = client.send_request(sent_request)
        sleep(0.1)

        client.stop()
        worker.stop()

        self.assertEqual(len(status_messages), 2)

        received_request_id = status_messages[0][0]
        for i, (request_id, header, request) in enumerate(status_messages):
            self.assertEqual(received_request_id, request_id)

            if i == 0:
                self.assertEqual(header['action'], ACTION_REQUEST_START)
            else:
                self.assertEqual(header['action'], ACTION_REQUEST_SUCCESS)
                self.assertEqual(header['message'], service_message)
