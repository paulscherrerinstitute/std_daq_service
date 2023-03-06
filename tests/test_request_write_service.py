import unittest
from time import sleep
import zmq

from std_daq_service.broker.client import BrokerClient
from std_daq_service.broker.common import TEST_BROKER_URL, ACTION_REQUEST_START, ACTION_REQUEST_SUCCESS
from std_daq_service.broker.primary_service import PrimaryBrokerService
from std_daq_service.protocol import ImageMetadata
from std_daq_service.writer_driver.service import RequestWriterService


class TestRequestWriteService(unittest.TestCase):

    def _setup_service(self, service_name, status_callback):
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

        listener = PrimaryBrokerService(broker_url=TEST_BROKER_URL,
                                        service_name=service_name,
                                        request_callback=service.on_request,
                                        kill_callback=service.on_kill)

        client = BrokerClient(broker_url=TEST_BROKER_URL,
                              tag=service_name,
                              status_callback=status_callback)
        return sender, receiver, listener, service, client

    def test_basic_workflow(self):
        service_name = 'test_service'
        request = {
            "n_images": 10,
            "output_file": "/test/output.h5"
        }

        def on_status_message(request_id, request, header):
            nonlocal last_header
            last_header = header
        last_header = None

        sender, receiver, listener, service, client = self._setup_service(service_name, on_status_message)
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
            sender.send(bytes(ImageMetadata(version, pulse_id, image_height, image_width, dtype, encoding)))

        for pulse_id in range(request["n_images"]):
            write_message = receiver.recv_json()

            self.assertEqual(write_message["output_file"], request["output_file"])
            self.assertEqual(write_message["n_images"], request['n_images'])
            self.assertEqual(write_message["i_image"], pulse_id)

        sleep(0.1)
        self.assertEqual(last_header['action'], ACTION_REQUEST_SUCCESS)

        sender.close()
        receiver.close()

        listener.stop()
        client.stop()

    def test_write_kill(self):

        service_name = 'kill_service'
        n_images = 10

        def on_status_message(request_id, request, header):
            nonlocal last_header
            last_header = header
        last_header = None

        sender, receiver, listener, service, client = self._setup_service(service_name, on_status_message)
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

    def test_multiple_requests(self):
        service_name = 'multi_service'
        n_images = 5

        def on_status_message(request_id, request, header):
            nonlocal last_header
            last_header = header
        last_header = None

        sender, receiver, listener, service, client = self._setup_service(service_name, on_status_message)
        sleep(0.1)

        # Send write request.
        first_request_id = client.send_request({
            "n_images": n_images,
            "output_file": "/test/output.h5"
        })
        sleep(0.1)
        self.assertEqual(last_header['action'], ACTION_REQUEST_START)

        # Send images into the transceiver.
        for pulse_id in range(n_images):
            sender.send(ImageMetadata(1, pulse_id, 1024, 512, 1, 1))
        sleep(0.1)

        # Receive the write request on the other side.
        for pulse_id in range(n_images):
            write_message = receiver.recv_json()
            self.assertEqual(write_message['i_image'], pulse_id)

        self.assertEqual(last_header['action'], ACTION_REQUEST_SUCCESS)
        last_header = None

        # Send images that will be ignored in between.
        for pulse_id in range(n_images, n_images*2):
            sender.send(ImageMetadata(1, pulse_id, 1024, 512, 1, 1))
        sleep(0.1)

        # Send another request.
        second_request_id = client.send_request({
            "n_images": n_images,
            "output_file": "/test/output.h5"
        })
        sleep(0.1)
        self.assertEqual(last_header['action'], ACTION_REQUEST_START)

        # But with 1 message in the stream less than we expected.
        for pulse_id in range(n_images*2, (n_images*3)-1):
            sender.send(ImageMetadata(1, pulse_id, 1024, 512, 1, 1))
        sleep(0.1)

        # Confirm the status did not already change.
        self.assertEqual(last_header['action'], ACTION_REQUEST_START)

        # Check if we received the partial write stream.
        for pulse_id in range(n_images*2, (n_images*3)-1):
            write_message = receiver.recv_json()
            # self.assertEqual(write_message['i_image'], pulse_id)

        # The first request id should not kill the request anymore.
        client.kill_request(first_request_id)
        sleep(0.2)

        # Verify the kill with the old request id did nothing.
        self.assertEqual(last_header['action'], ACTION_REQUEST_START)

        # This is the correct request id to kill
        client.kill_request(second_request_id)
        sleep(0.2)

        # Verify the kill with the old request id did nothing.
        self.assertEqual(last_header['action'], ACTION_REQUEST_SUCCESS)

        # The termination message has i_image == n_images
        write_message = receiver.recv_json()
        # self.assertEqual(write_message['i_image'], n_images)

        sender.close()
        receiver.close()

        listener.stop()
        client.stop()
