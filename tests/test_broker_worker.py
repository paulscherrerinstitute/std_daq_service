import unittest
from time import sleep

from std_daq_service.broker.client import BrokerClient
from std_daq_service.broker.common import TEST_BROKER_URL, ACTION_REQUEST_SUCCESS, ACTION_REQUEST_START, \
    ACTION_REQUEST_FAIL
from std_daq_service.broker.service import BrokerService


class TestBrokerListener(unittest.TestCase):
    def test_basic_workflow(self):

        request = {"just": "a", "request": "yeey"}
        service_name = "testing_service"
        service_tag = "psi.facility.beamline"

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

        worker = BrokerService(TEST_BROKER_URL,
                               tag=service_tag,
                               service_name=service_name,
                               request_callback=on_request_message)

        client = BrokerClient(broker_url=TEST_BROKER_URL,
                              tag=service_tag,
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

        request = {"just": "a", "request": "yeey"}
        # service_name = "killable_service"
        # service_tag = "psi.facility.beamline.#"
        # request_tag = "psi.facility.beamline.profile"
        # status_tag = "psi.facility.beamline.#"
        #
        # error_message = "This is an expected error. Carry on."
        #
        # status_messages = []
        #
        # def on_status_message(request_id, header, received_request):
        #     nonlocal sent_request_id
        #     nonlocal status_messages
        #
        #     self.assertEqual(request_id, sent_request_id)
        #     self.assertEqual(header['source'], service_name)
        #
        #     if received_request:
        #         self.assertEqual(request, received_request)
        #
        #     status_messages.append(header)
        #
        # def on_request_message(request_id, received_request):
        #     nonlocal sent_request_id
        #
        #     self.assertEqual(request_id, sent_request_id)
        #
        #     # This is how we test a failing service.
        #     if not received_request:
        #         raise ValueError(error_message)
        #     else:
        #         self.assertEqual(request, received_request)
        #
        # def on_kill_message(request_id):
        #     pass
        #
        # worker = BrokerWorker(broker_config.TEST_BROKER_URL,
        #                       request_tag=service_tag,
        #                       name=service_name,
        #                       on_request_message_function=on_request_message)
        # t_worker = Thread(target=worker.start)
        # t_worker.start()
        #
        # client = BrokerClient(broker_url=broker_config.TEST_BROKER_URL,
        #                       status_tag=status_tag,
        #                       on_status_message_function=on_status_message)
        # t_client = Thread(target=client.start)
        # t_client.start()
        #
        # sleep(0.1)
        #
        # sent_request_id = client.send_request(request_tag, request)
        # sleep(0.1)
        #
        # sent_request_id = client.send_request(request_tag, None)
        # sleep(0.1)
        #
        # client.stop()
        # t_client.join()
        #
        # worker.stop()
        # t_worker.join()
        #
        # expected_status_actions = [broker_config.ACTION_REQUEST_START,
        #                            broker_config.ACTION_REQUEST_SUCCESS,
        #                            broker_config.ACTION_REQUEST_START,
        #                            broker_config.ACTION_REQUEST_FAIL]
        #
        # for i, expected_action in enumerate(expected_status_actions):
        #     self.assertEqual(expected_action,
