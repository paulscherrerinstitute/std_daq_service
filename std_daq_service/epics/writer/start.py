import argparse
import logging

from std_daq_service.broker.common import TEST_BROKER_URL
from std_daq_service.broker.service import BrokerService
from std_daq_service.epics.writer.service import EpicsWriterService

_logger = logging.getLogger("EpicsWriter")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Epics writer.')

    parser.add_argument("service_name", type=str, help="Name of the service")
    parser.add_argument("service_tag", type=str, help="Where to bind the service")
    parser.add_argument("buffer_folder", type=str, help="Path to the Epics buffer wou want to write from.")

    parser.add_argument("--broker_url", default=TEST_BROKER_URL,
                        help="Address of the broker to connect to.")
    parser.add_argument("--log_level", default="INFO",
                        choices=['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG'],
                        help="Log level to use.")

    args = parser.parse_args()

    _logger.setLevel(args.log_level)
    logging.getLogger("pika").setLevel(logging.WARNING)

    _logger.info(f'Service {args.service_name} connecting to {args.broker_url}.')

    service = EpicsWriterService(buffer_folder=args.buffer_folder)

    listener = BrokerService(broker_url=args.broker_url,
                             tag=args.service_tag,
                             service_name=args.service_name,
                             request_callback=service.on_request,
                             kill_callback=service.on_kill)

    try:
        listener.block()
    except KeyboardInterrupt:
        pass

    listener.stop()

    _logger.info(f'Service {args.service_name} stopping.')
