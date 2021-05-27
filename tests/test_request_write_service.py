import json
import unittest
from threading import Thread
from time import sleep
import zmq

from sf_daq_service.common import broker_config
from sf_daq_service.common.broker_consumer_client import BrokerConsumerListener
from sf_daq_service.writer_agent.transceiver import Transceiver
from sf_daq_service.writer_agent.format import ImageMetadata
from sf_daq_service.writer_agent.request_write_service import RequestWriterService
from tests.utils import get_test_broker


class TestRequestWriteService(unittest.TestCase):
    def test_basic_workflow(self):

        input_stream_url = "tcp://127.0.0.1:7000"
        output_stream_url = "tcp://127.0.0.1:7001"
        service_name = "test_service"

        request = {
            "n_images": 10,
            "output_file": "/test/output.h5"
        }

        transceiver = None
        listener = None
        client = None
        thread = None

        try:
            ctx = zmq.Context()

            sender = ctx.socket(zmq.PUB)
            sender.bind(input_stream_url)

            receiver = ctx.socket(zmq.SUB)
            receiver.connect(output_stream_url)
            receiver.setsockopt_string(zmq.SUBSCRIBE, "")

            clinet, channel, queue = get_test_broker()

            def service_thread():
                nonlocal transceiver
                nonlocal listener
                nonlocal service_name

                service = RequestWriterService()

                transceiver = Transceiver(input_stream_url=input_stream_url,
                                          output_stream_url=output_stream_url,
                                          on_message_function=service.on_stream_message)

                listener = BrokerConsumerListener(broker_url=broker_config.TEST_BROKER_URL,
                                                  service_name=service_name,
                                                  on_message_function=service.on_broker_message)

                listener.start_consuming()

            thread = Thread(target=service_thread)
            thread.start()
            sleep(0.1)

            channel.basic_publish(exchange=broker_config.REQUEST_EXCHANGE,
                                  routing_key=service_name,
                                  body=json.dumps(request).encode())

            sleep(0.1)

            for pulse_id in range(request["n_images"]):
                sender.send(ImageMetadata(pulse_id, 0, 0, 0))

            for pulse_id in range(request["n_images"]):
                write_message = receiver.recv_json()

                self.assertEqual(write_message["i_image"], write_message["image_metadata"]["pulse_id"])
                self.assertEqual(write_message["i_image"], pulse_id)
                self.assertEqual(write_message["output_file"], request["output_file"])
                # TODO: Test also image metadata.

        finally:
            if transceiver is not None:
                transceiver.stop()

            if listener is not None:
                listener.stop()

            if thread is not None:
                thread.join()

            if client:
                client.close()
