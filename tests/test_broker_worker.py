import unittest
from time import sleep

from std_daq_service.broker.client import BrokerClient
from std_daq_service.broker.common import TEST_BROKER_URL, ACTION_REQUEST_SUCCESS, ACTION_REQUEST_START, \
    ACTION_REQUEST_FAIL
from std_daq_service.broker.primary_service import PrimaryBrokerService


class TestBrokerListener(unittest.TestCase):
    def test_basic_workflow(self):

        request = {"just": "a", "request": "yeey"}
        service_name = "testing_service"

        error_message = "This is an expected error. Carry on."

        status_messages = []

        def on_status_message(request_id, received_request, header):
            nonlocal sent_request_id
            nonlocal status_messages

            self.assertEqual(request_id, sent_request_id)
            self.assertEqual(header['source'], service_name)

            if received_request:
                self.assertEqual(request, received_request)

            status_messages.append(header)

        def on_request_message(request_id, received_request):
            nonlocal sent_request_id

            self.assertEqual(request_id, sent_request_id)

            # This is how we test a failing service.
            if not received_request:
                raise ValueError(error_message)
            else:
                self.assertEqual(request, received_request)

        worker = PrimaryBrokerService(TEST_BROKER_URL,
                                      service_name=service_name,
                                      request_callback=on_request_message)

        client = BrokerClient(broker_url=TEST_BROKER_URL,
                              tag=service_name,
                              status_callback=on_status_message)

        sleep(0.1)
        sent_request_id = client.send_request(request)
        sleep(0.1)

        sent_request_id = client.send_request(None)
        sleep(0.1)

        client.stop()
        worker.stop()

        expected_status_actions = [ACTION_REQUEST_START,
                                   ACTION_REQUEST_SUCCESS,
                                   ACTION_REQUEST_START,
                                   ACTION_REQUEST_FAIL]

        for i, expected_action in enumerate(expected_status_actions):
            self.assertEqual(expected_action, status_messages[i]['action'])

    def test_kill_workflow(self):

        request = {"just": "a", "request": "kill"}
        service_name = "killable_service"

        status_messages = []

        def on_status_message(request_id, received_request, header):
            nonlocal status_messages
            status_messages.append(header)

        def on_request_message(request_id, received_request):
            sleep(0.1)
            self.assertTrue(kill_flag)

        def on_kill_message(request_id):
            nonlocal sent_request_id, kill_flag
            self.assertEqual(request_id, sent_request_id)
            kill_flag = True
        kill_flag = False

        worker = PrimaryBrokerService(TEST_BROKER_URL,
                                      service_name=service_name,
                                      request_callback=on_request_message,
                                      kill_callback=on_kill_message)

        client = BrokerClient(broker_url=TEST_BROKER_URL,
                              tag=service_name,
                              status_callback=on_status_message)

        sleep(0.1)
        sent_request_id = client.send_request(request)
        client.kill_request(sent_request_id)
        sleep(0.2)

        self.assertEqual(len(status_messages), 2)

        client.stop()
        worker.stop()


