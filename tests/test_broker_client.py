import unittest
from threading import Thread
from time import sleep

from sf_daq_service.common import broker_config
from sf_daq_service.common.broker_client import BrokerClient
from sf_daq_service.common.broker_worker import BrokerWorker


class TestBrokerListener(unittest.TestCase):
    def test_broker_listener_workflow(self):
        service_name = "psi.facility.beamline.profile.echo"
        request_tag = "psi.facility.beamline.profile.echo"
        status_tag = "psi.facility.beamline.#"

        sent_request = {
            "this is a": 'request'
        }
        service_message = "IT WORKS!!"

        status_messages = []

        def on_status_message(request_id, header, request):
            self.assertEqual(header["source"], service_name)

            status_messages.append((request_id, header, request))

        def on_service_message(request):
            self.assertEqual(sent_request, request)
            return service_message

        client = BrokerClient(broker_url=broker_config.TEST_BROKER_URL,
                              tag=status_tag,
                              on_message_function=on_status_message)

        worker = BrokerWorker(broker_url=broker_config.TEST_BROKER_URL,
                              service_name=service_name,
                              on_message_function=on_service_message)

        t_client = Thread(target=client.start)
        t_client.start()

        t_worker = Thread(target=worker.start)
        t_worker.start()

        sleep(0.1)
        client.send_request(request_tag, {}, sent_request)
        sleep(0.1)

        client.stop()
        worker.stop()

        t_client.join()
        t_worker.join()

        self.assertEqual(len(status_messages), 2)

        received_request_id = status_messages[0][0]
        for i, (request_id, header, request) in enumerate(status_messages):
            self.assertEqual(received_request_id, request_id)

            if i == 0:
                self.assertEqual(header['action'], broker_config.ACTION_REQUEST_START)
            else:
                self.assertEqual(header['action'], broker_config.ACTION_REQUEST_SUCCESS)
                self.assertEqual(header['message'], service_message)

