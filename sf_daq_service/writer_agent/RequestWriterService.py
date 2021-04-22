import argparse
import logging
from threading import Event

from sf_daq_service.common import broker_config
from sf_daq_service.common.broker_listener import BrokerListener
from sf_daq_service.common.transceiver import Transceiver
from sf_daq_service.writer_agent.format import ImageMetadata, WriterStreamMessage, WriteMetadata

_logger = logging.getLogger('RequestWriteService')


class RequestWriterService(object):
    def __init__(self):
        self.write_request = None
        self.request = None
        self.request_completed = Event()

        self.i_image = None

    def on_stream_message(self, recv_bytes: bytes):
        if self.request is None:
            return None

        if self.i_image is None:
            self.i_image = 0

        image_meta = ImageMetadata.from_buffer_copy(recv_bytes)

        write_meta = WriteMetadata(self.request["run_id"],
                                   self.i_image,
                                   self.request["n_images"])

        if self.i_image + 1 == self.request["n_images"]:
            self._complete_request()

        return WriterStreamMessage(image_meta, write_meta)

    def _complete_request(self):
        self.request = None
        self.i_image = None
        self.request_completed.set()

    def on_broker_message(self, request):
        self._wait_on_request(request)
        self.request_completed.clear()

    def _wait_on_request(self, request):
        _logger.info(f"Starting to work on request {request}")
        self.request = request
        self.request_completed.wait()


if __file__ == "__main__":
    parser = argparse.ArgumentParser(description='Broker service starter.')

    parser.add_argument("service_name", type=str, help="Name of the service")
    parser.add_argument("--broker_url", default=broker_config.DEFAULT_BROKER_URL,
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
