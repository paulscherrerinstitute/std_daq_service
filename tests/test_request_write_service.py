import json
import unittest
from threading import Thread
from time import sleep
import zmq

from sf_daq_service.common import broker_config
from sf_daq_service.common.broker_client import BrokerClient
from sf_daq_service.common.broker_worker import BrokerWorker
from sf_daq_service.writer_agent.zmq_transciever import ZmqTransciever
from sf_daq_service.writer_agent.start import RequestWriterService, ImageMetadata


class TestRequestWriteService(unittest.TestCase):
    def test_basic_workflow(self):

        input_stream_url = "tcp://127.0.0.1:7000"
        output_stream_url = "tcp://127.0.0.1:7001"
        service_name = "test_service"

        request = {
            "n_images": 10,
            "output_file": "/test/output.h5"
        }

        ctx = zmq.Context()

        sender = ctx.socket(zmq.PUB)
        sender.bind(input_stream_url)

        receiver = ctx.socket(zmq.SUB)
        receiver.connect(output_stream_url)
        receiver.setsockopt_string(zmq.SUBSCRIBE, "")

        service = RequestWriterService()

        transceiver = ZmqTransciever(input_stream_url=input_stream_url,
                                     output_stream_url=output_stream_url,
                                     on_message_function=service.on_stream_message)

        listener = BrokerWorker(broker_url=broker_config.TEST_BROKER_URL,
                                name=service_name,
                                request_tag=service_name,
                                on_request_message_function=service.on_broker_message)
        t_service = Thread(target=listener.start)
        t_service.start()

        client = BrokerClient(broker_url=broker_config.TEST_BROKER_URL,
                              status_tag="*",
                              on_status_message_function=lambda x, y, z: x)
        t_client = Thread(target=client.start)
        t_client.start()
        sleep(0.1)

        client.send_request(service_name, request)
        sleep(0.1)

        for pulse_id in range(request["n_images"]):
            sender.send(ImageMetadata(pulse_id, 0, 0, 0))

        for pulse_id in range(request["n_images"]):
            write_message = receiver.recv_json()

            self.assertEqual(write_message["i_image"], write_message["image_metadata"]["pulse_id"])
            self.assertEqual(write_message["i_image"], pulse_id)
            self.assertEqual(write_message["output_file"], request["output_file"])
            # TODO: Test also image metadata.

        transceiver.stop()

        listener.stop()
        t_service.join()

        client.stop()
        t_client.join()

        receiver.close()
        sender.close()
