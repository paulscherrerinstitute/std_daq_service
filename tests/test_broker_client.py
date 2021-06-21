import unittest
from threading import Thread
from time import sleep

from std_daq_service.broker_client import BrokerClient, TEST_BROKER_URL, ACTION_REQUEST_SUCCESS, \
    ACTION_REQUEST_START
from std_daq_service.common.broker_worker import BrokerWorker


class TestBrokerListener(unittest.TestCase):
    def test_broker_listener_workflow(self):
        service_name = "noop_worker"
        service_tag = "psi.facility.beamline.#"
        request_tag = "psi.facility.beamline.profile"
        status_tag = "psi.facility.beamline.#"

        sent_request = {
            "this is a": 'request'
        }
        service_message = "IT WORKS!!"

        status_messages = []

        def on_status_message(request_id, header, request):
            self.assertEqual(header["source"], service_name)

            status_messages.append((request_id, header, request))

        def on_service_message(request_id, request):
            self.assertEqual(sent_request, request)
            return service_message

        client = BrokerClient(broker_url=TEST_BROKER_URL,
                              tag=status_tag,
                              status_callback=on_status_message)

        worker = BrokerWorker(broker_url=TEST_BROKER_URL,
                              request_tag=service_tag,
                              name=service_name,
                              on_request_message_function=on_service_message)

        t_worker = Thread(target=worker.start)
        t_worker.start()

        sleep(0.1)
        client.send_request(sent_request)
        sleep(0.1)

        client.stop()
        worker.stop()

        t_worker.join()

        self.assertEqual(len(status_messages), 2)

        received_request_id = status_messages[0][0]
        for i, (request_id, header, request) in enumerate(status_messages):
            self.assertEqual(received_request_id, request_id)

            if i == 0:
                self.assertEqual(header['action'], ACTION_REQUEST_START)
            else:
                self.assertEqual(header['action'], ACTION_REQUEST_SUCCESS)
                self.assertEqual(header['message'], service_message)

