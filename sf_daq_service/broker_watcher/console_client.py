import argparse
import logging

from sf_daq_service.broker_watcher.status_listener import StatusListener
from sf_daq_service.common import broker_config
from sf_daq_service.common.broker_listener_client import BrokerListenerClient

_logger = logging.getLogger("BrokerListenerConsoleClient")


def print_to_console(message):
    print(message)


def start_console_output(tag, broker_url):
    listener = StatusListener(on_status_change_function=print_to_console)
    client = BrokerListenerClient(broker_url=broker_url,
                                  tag=tag,
                                  on_message_function=listener.on_broker_message)

    try:
        client.start()
    except KeyboardInterrupt:
        client.stop()


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

