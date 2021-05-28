import argparse
import logging

from sf_daq_service.watcher.status_aggregator import StatusAggregator
from sf_daq_service.common import broker_config
from sf_daq_service.common.broker_client import BrokerClient

_logger = logging.getLogger("BrokerListenerConsoleClient")


def print_to_console(message):
    print(message)


def start_console_output(tag, broker_url):
    aggregator = StatusAggregator(on_status_change_function=print_to_console)
    client = BrokerClient(broker_url=broker_url,
                          status_tag=tag,
                          on_status_message_function=aggregator.on_broker_message)

    client.start()


if __file__ == "__main__":
    parser = argparse.ArgumentParser(description='Broker Watcher')

    parser.add_argument("tag", type=str, default="#", help="Tag to bind to on the status exchange.")
    parser.add_argument("--broker_url", default=broker_config.TEST_BROKER_URL,
                        help="Address of the broker to connect to.")
    parser.add_argument("--log_level", default="ERROR",
                        choices=['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG'],
                        help="Log level to use.")

    args = parser.parse_args()

    _logger.setLevel(args.log_level)
    logging.getLogger("pika").setLevel(logging.WARNING)

    start_console_output(tag=args.tag, broker_url=args.broker_url)
