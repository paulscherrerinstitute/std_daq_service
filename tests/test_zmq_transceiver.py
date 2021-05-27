import unittest
from time import sleep

import zmq

from sf_daq_service.writer_agent.start import ImageMetadata
from sf_daq_service.writer_agent.zmq_transciever import ZmqTransciever


class TestTransceiver(unittest.TestCase):

    def test_basic_workflow(self):

        input_stream_url = "tcp://127.0.0.1:7000"
        output_stream_url = 'tcp://127.0.0.1:7001'

        request = {
            "n_images": 10,
            "output_file": "/test/output.h5"
        }

        transceiver = None

        try:
            ctx = zmq.Context()

            sender = ctx.socket(zmq.PUB)
            sender.bind(input_stream_url)

            receiver = ctx.socket(zmq.SUB)
            receiver.connect(output_stream_url)
            receiver.setsockopt_string(zmq.SUBSCRIBE, "")

            i_image = 0

            def process_message(recv_bytes: bytes):
                nonlocal i_image
                image_meta = ImageMetadata.from_buffer_copy(recv_bytes)

                writer_stream_message = {
                    "output_file": request["output_file"],
                    "i_image": i_image,
                    "n_images": request["n_images"],
                    "image_metadata": image_meta.as_dict()
                }

                i_image += 1

                return writer_stream_message

            transceiver = ZmqTransciever(input_stream_url, output_stream_url, process_message)
            sleep(0.3)

            for pulse_id in range(request["n_images"]):
                sender.send(ImageMetadata(pulse_id, 0, 0, 0))

            for pulse_id in range(request["n_images"]):
                write_message = receiver.recv_json()
                self.assertEqual(write_message["i_image"], write_message["image_metadata"]["pulse_id"])

        finally:
            if transceiver:
                transceiver.stop()
