import json
import unittest
from threading import Thread
from time import sleep

from sf_daq_service.common import broker_config
from sf_daq_service.common.broker_client import BrokerClient
from sf_daq_service.common.broker_worker import BrokerWorker


class TestBrokerListener(unittest.TestCase):
    def test_basic_workflow(self):

        request = {"just": "a", "request": "yeey"}
        service_name = "testing_service"
        service_tag = "psi.facility.beamline.#"
        request_tag = "psi.facility.beamline.profile"
        status_tag = "psi.facility.beamline.#"

        error_message = "This is an expected error. Carry on."

        status_messages = []

        def on_status_message(request_id, header, received_request):
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

        worker = BrokerWorker(broker_config.TEST_BROKER_URL,
                              request_tag=service_tag,
                              name=service_name,
                              on_request_message_function=on_request_message)
        t_worker = Thread(target=worker.start)
        t_worker.start()

        client = BrokerClient(broker_url=broker_config.TEST_BROKER_URL,
                              status_tag=status_tag,
                              on_status_message_function=on_status_message)
        t_client = Thread(target=client.start)
        t_client.start()

        sleep(0.1)

        sent_request_id = client.send_request(request_tag, request)
        sleep(0.1)

        sent_request_id = client.send_request(request_tag, None)
        sleep(0.1)

        client.stop()
        t_client.join()

        worker.stop()
        t_worker.join()

        expected_status_actions = [broker_config.ACTION_REQUEST_START,
                                   broker_config.ACTION_REQUEST_SUCCESS,
                                   broker_config.ACTION_REQUEST_START,
                                   broker_config.ACTION_REQUEST_FAIL]

        for i, expected_action in enumerate(expected_status_actions):
            self.assertEqual(expected_action, status_messages[i]['action'])

    def test_kill_workflow(self):

        request = {"just": "a", "request": "yeey"}
        service_name = "killable_service"
        service_tag = "psi.facility.beamline.#"
        request_tag = "psi.facility.beamline.profile"
        status_tag = "psi.facility.beamline.#"

        error_message = "This is an expected error. Carry on."

        status_messages = []

        def on_status_message(request_id, header, received_request):
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

        def on_kill_message(request_id):


            worker = BrokerWorker(broker_config.TEST_BROKER_URL,
                                  request_tag=service_tag,
                                  name=service_name,
                                  on_request_message_function=on_request_message)
            t_worker = Thread(target=worker.start)
            t_worker.start()

            client = BrokerClient(broker_url=broker_config.TEST_BROKER_URL,
                                  status_tag=status_tag,
                                  on_status_message_function=on_status_message)
            t_client = Thread(target=client.start)
            t_client.start()

            sleep(0.1)

            sent_request_id = client.send_request(request_tag, request)
            sleep(0.1)

            sent_request_id = client.send_request(request_tag, None)
            sleep(0.1)

            client.stop()
            t_client.join()

            worker.stop()
            t_worker.join()

            expected_status_actions = [broker_config.ACTION_REQUEST_START,
                                       broker_config.ACTION_REQUEST_SUCCESS,
                                       broker_config.ACTION_REQUEST_START,
                                       broker_config.ACTION_REQUEST_FAIL]

            for i, expected_action in enumerate(expected_status_actions):
                self.assertEqual(expected_action,