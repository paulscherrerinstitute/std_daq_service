import unittest
from time import sleep

import zmq

from sf_daq_service.common.transceiver import Transceiver
from sf_daq_service.writer_agent.format import ImageMetadata, WriterStreamMessage, WriteMetadata


class TestTransceiver(unittest.TestCase):

    def test_basic_workflow(self):
        input_stream_url = "tcp://127.0.0.1:7000"
        output_stream_url = 'tcp://127.0.0.1:7001'
        n_images = 10

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

            write_meta = WriteMetadata(
                run_id=100,
                i_image=i_image,
                n_images=n_images,
                image_y_size=100,
                image_x_size=100,
                bits_per_pixel=100)

            i_image += 1

            return WriterStreamMessage(image_meta, write_meta)

        transceiver = Transceiver(input_stream_url, output_stream_url, process_message)
        sleep(0.5)

        for pulse_id in range(n_images):
            sender.send(ImageMetadata(pulse_id, 0, 0, 0))

        for pulse_id in range(n_images):
            msg = WriterStreamMessage.from_buffer_copy(receiver.recv())
            self.assertEqual(pulse_id, msg.image_meta.pulse_id)
            self.assertEqual(pulse_id, msg.write_meta.i_image)

        transceiver.stop()
