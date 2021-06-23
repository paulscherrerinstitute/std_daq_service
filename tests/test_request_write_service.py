import unittest
from time import sleep
import zmq

from std_daq_service.broker.client import BrokerClient
from std_daq_service.broker.common import TEST_BROKER_URL, ACTION_REQUEST_START, ACTION_REQUEST_SUCCESS
from std_daq_service.broker.service import BrokerService
from std_daq_service.protocol import ImageMetadata
from std_daq_service.writer_agent.service import RequestWriterService


class TestRequestWriteService(unittest.TestCase):

    def _setup_service(self, tag, service_name, status_callback):
        input_stream_url = "tcp://127.0.0.1:7000"
        output_stream_url = "tcp://127.0.0.1:7001"

        ctx = zmq.Context()

        sender = ctx.socket(zmq.PUB)
        sender.bind(input_stream_url)

        receiver = ctx.socket(zmq.SUB)
        receiver.connect(output_stream_url)
        receiver.setsockopt_string(zmq.SUBSCRIBE, "")

        service = RequestWriterService(input_stream_url=input_stream_url,
                                       output_stream_url=output_stream_url)

        listener = BrokerService(broker_url=TEST_BROKER_URL,
                                 tag=tag,
                                 service_name=service_name,
                                 request_callback=service.on_request,
                                 kill_callback=service.on_kill)

        client = BrokerClient(broker_url=TEST_BROKER_URL,
                              tag=tag,
                              status_callback=status_callback)
        return sender, receiver, listener, service, client

    def test_basic_workflow(self):
        tag = 'test_service'
        request = {
            "n_images": 10,
            "output_file": "/test/output.h5"
        }

        def on_status_message(request_id, request, header):
            nonlocal last_header
            last_header = header
        last_header = None

        sender, receiver, listener, service, client = self._setup_service(tag, tag, on_status_message)
        sleep(0.1)

        client.send_request(request)
        sleep(0.1)

        self.assertEqual(last_header['action'], ACTION_REQUEST_START)

        version = 1
        image_height = 1024
        image_width = 512
        dtype = 1
        encoding = 2

        for pulse_id in range(request["n_images"]):
            sender.send(ImageMetadata(version, pulse_id, image_height, image_width, dtype, encoding))

        for pulse_id in range(request["n_images"]):
            write_message = receiver.recv_json()

            self.assertEqual(write_message["i_image"], write_message["image_metadata"]["id"])
            self.assertEqual(write_message["i_image"], pulse_id)
            self.assertEqual(write_message["output_file"], request["output_file"])

            self.assertEqual(write_message['image_metadata']["version"], version)
            self.assertEqual(write_message['image_metadata']["height"], image_height)
            self.assertEqual(write_message['image_metadata']["width"], image_width)
            self.assertEqual(write_message['image_metadata']["dtype"], dtype)
            self.assertEqual(write_message['image_metadata']["encoding"], encoding)

        sleep(0.1)
        self.assertEqual(last_header['action'], ACTION_REQUEST_SUCCESS)

        sender.close()
        receiver.close()

        listener.stop()
        client.stop()

    def test_write_kill(self):

        tag = 'kill_service'
        n_images = 10

        def on_status_message(request_id, request, header):
            nonlocal last_header
            last_header = header
        last_header = None

        sender, receiver, listener, service, client = self._setup_service(tag, tag, on_status_message)
        sleep(0.1)

        for pulse_id in range(5):
            sender.send(ImageMetadata(1, pulse_id, 1024, 512, 1, 1))

        request_id = client.send_request({
            "n_images": n_images,
            "output_file": "/test/output.h5"
        })
        sleep(0.1)

        self.assertEqual(last_header['action'], ACTION_REQUEST_START)

        for pulse_id in range(5, n_images):
            sender.send(ImageMetadata(1, pulse_id, 1024, 512, 1, 1))
        sleep(0.1)

        # Confirm the status did not already change.
        self.assertEqual(last_header['action'], ACTION_REQUEST_START)

        client.kill_request(request_id)
        sleep(0.2)

        self.assertEqual(last_header['action'], ACTION_REQUEST_SUCCESS)

        sender.close()
        receiver.close()

        listener.stop()
        client.stop()
