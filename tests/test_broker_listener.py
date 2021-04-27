import json
import unittest
from threading import Thread
from time import sleep

from sf_daq_service.common import broker_config
from sf_daq_service.common.broker_listener import BrokerListener
from tests.utils import get_test_broker


class TestBrokerListener(unittest.TestCase):
    def test_basic_workflow(self):

        thread = None
        listener = None

        try:
            request = {
                "just": "a",
                "request": "yeey"
            }

            service_name = "testing_service"
            error_message = "This is an expected error. Carry on."

            def on_message(received_request):
                # This is how we test a failing service.
                if not received_request:
                    raise ValueError(error_message)
                else:
                    self.assertEqual(request, received_request)

            listener = None

            def listener_thread():
                nonlocal listener
                listener = BrokerListener(broker_config.TEST_BROKER_URL, service_name, on_message)
                listener.start_consuming()

            thread = Thread(target=listener_thread)
            thread.start()
            sleep(0.1)

            channel, queue = get_test_broker()
            channel.basic_publish(exchange=broker_config.REQUEST_EXCHANGE,
                                  routing_key=service_name,
                                  body=json.dumps(request).encode())

            sleep(0.1)

            def check_status_queue(action, expected_request):
                method_frame, header_frame, body = channel.basic_get(queue=queue)
                channel.basic_ack(delivery_tag=method_frame.delivery_tag)

                self.assertEqual(json.loads(body.decode()), expected_request)
                self.assertEqual(header_frame.headers["action"], action)
                self.assertEqual(header_frame.headers["source"], service_name)

                return header_frame.headers["message"]

            check_status_queue(broker_config.ACTION_REQUEST_START, request)
            check_status_queue(broker_config.ACTION_REQUEST_SUCCESS, request)

            channel.basic_publish(exchange=broker_config.REQUEST_EXCHANGE,
                                  routing_key=service_name,
                                  body=json.dumps({}).encode())

            sleep(0.1)

            check_status_queue(broker_config.ACTION_REQUEST_START, {})
            message = check_status_queue(broker_config.ACTION_REQUEST_FAIL, {})
            self.assertEqual(message, error_message)

        finally:
            if listener:
                listener.stop()

            if thread:
                thread.join()
