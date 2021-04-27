import argparse
import logging
from threading import Event

from sf_daq_service.common import broker_config
from sf_daq_service.common.broker_listener import BrokerListener
from sf_daq_service.common.transceiver import Transceiver
from sf_daq_service.writer_agent.format import ImageMetadata

_logger = logging.getLogger('RequestWriteService')


class RequestWriterService(object):
    def __init__(self):
        self.write_request = None
        self.request = None
        self.request_completed = Event()
        self.request_result = None

        self.i_image = None

    def on_stream_message(self, recv_bytes: bytes):
        if self.request is None:
            return None

        image_meta = ImageMetadata.from_buffer_copy(recv_bytes)

        if self.i_image is None:
            self.i_image = 0
            self.request_result = {
                'start_pulse_id': image_meta.pulse_id,
                'n_images': self.request['n_images'],
                'output_file': self.request["output_file"]
            }

        writer_stream_message = {
            "output_file": self.request["output_file"],
            "i_image": self.i_image,
            "n_images": self.request["n_images"],
            "image_metadata": image_meta.as_dict()
        }

        if self.i_image + 1 == self.request["n_images"]:
            self.request_result["end_pulse_id"] = image_meta.pulse_id
            self._complete_request()
        else:
            self.i_image += 1

        return writer_stream_message

    def _complete_request(self):
        self.request = None
        self.i_image = None
        self.request_completed.set()

    def on_broker_message(self, request):
        self._set_request_and_wait(request)
        self.request_completed.clear()

        return self.request_result

    def _set_request_and_wait(self, request):
        _logger.info(f"Starting to work on request {request}")
        self.request_result = None
        self.request = request
        self.request_completed.wait()


if __file__ == "__main__":
    parser = argparse.ArgumentParser(description='Broker service starter.')

    parser.add_argument("service_name", type=str, help="Name of the service")
    parser.add_argument("--broker_url", default=broker_config.TEST_BROKER_URL,
                        help="Address of the broker to connect to.")
    parser.add_argument("--log_level", default="INFO",
                        choices=['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG'],
                        help="Log level to use.")

    args = parser.parse_args()

    _logger.setLevel(args.log_level)
    logging.getLogger("pika").setLevel(logging.WARNING)

    _logger.info(f'Service {args.service_name} connecting to {args.broker_url}.')

    # TODO: Bring this 2 parameters in.
    input_stream = ''
    output_stream = ''

    service = RequestWriterService()

    transceiver = Transceiver(input_stream_url=input_stream,
                              output_stream_url=output_stream,
                              on_message_function=service.on_stream_message)

    listener = BrokerListener(broker_url=args.broker_url,
                              service_name=args.service_name,
                              on_message_function=service.on_broker_message)

    # Blocking call.
    listener.start_consuming()

    transceiver.stop()
    _logger.info(f'Service {args.service_name} stopping.')
