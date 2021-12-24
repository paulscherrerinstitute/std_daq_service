import argparse
import logging

from std_daq_service.broker.common import TEST_BROKER_URL
from std_daq_service.broker.primary_service import PrimaryBrokerService
from std_daq_service.writer_agent.service import RequestWriterService

_logger = logging.getLogger('RequestWriteService')

IPC_URL_BASE = "ipc:///tmp/std-daq-"
INPUT_IPC_URL_SUFFIX = "-assembler"
OUTPUT_IPC_URL_SUFFIX = "-writer_agent"

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Broker service starter.')

    parser.add_argument("service_name", type=str, help="Name of the service")
    parser.add_argument("detector_name", type=str, help="Name of the detector to write.")

    parser.add_argument("--broker_url", default=TEST_BROKER_URL,
                        help="Address of the broker to connect to.")
    parser.add_argument("--log_level", default="INFO",
                        choices=['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG'],
                        help="Log level to use.")

    args = parser.parse_args()

    _logger.setLevel(args.log_level)
    logging.getLogger("pika").setLevel(logging.WARNING)

    _logger.info(f'Service {args.service_name} connecting to {args.broker_url}.')

    input_stream = IPC_URL_BASE + args.detector_name + INPUT_IPC_URL_SUFFIX
    output_stream = IPC_URL_BASE + args.detector_name + OUTPUT_IPC_URL_SUFFIX

    _logger.info(f"Receiving from {input_stream} and sending data to {output_stream}.")

    service = RequestWriterService(input_stream_url=input_stream,
                                   output_stream_url=output_stream)

    listener = PrimaryBrokerService(broker_url=args.broker_url,
                                    service_name=args.service_name,
                                    request_callback=service.on_request,
                                    kill_callback=service.on_kill)

    try:
        listener.block()
    except KeyboardInterrupt:
        pass

    listener.stop()

    _logger.info(f'Service {args.service_name} stopping.')
