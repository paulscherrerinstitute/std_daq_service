import argparse
import logging

from sf_daq_service.watcher.status_aggregator import StatusAggregator
from sf_daq_service.common import broker_config
from sf_daq_service.common.broker_client import BrokerClient

_logger = logging.getLogger("BrokerListenerConsoleClient")

RESET = u"\u001b[0m"

GREEN_TEXT = u'\u001b[32m'
YELLOW_TEXT = u'\u001b[33m'
RED_TEXT = u'\u001b[31m'
BLACK_TEXT = u'\u001b[31m'

GREEN_BACKGROUND = u'\u001b[42m'
YELLOW_BACKGROUND = u'\u001b[43;1m'
RED_BACKGROUND = u'\u001b[41m'

status_symbol_mapping = {
    broker_config.ACTION_REQUEST_START: BLACK_TEXT + YELLOW_BACKGROUND + '*' + RESET,
    broker_config.ACTION_REQUEST_SUCCESS: GREEN_BACKGROUND + '+' + RESET,
    broker_config.ACTION_REQUEST_FAIL: RED_BACKGROUND + '-' + RESET
}

text_color_mapping = {
    broker_config.ACTION_REQUEST_START: YELLOW_TEXT,
    broker_config.ACTION_REQUEST_SUCCESS: GREEN_TEXT,
    broker_config.ACTION_REQUEST_FAIL: RED_TEXT
}

def print_to_console(request_id, status):
    services_output = ""
    status_indicators = ""
    for service_name, statuses in sorted(status['services'].items()):
        last_received_status = statuses[-1][0]

        status_indicators += status_symbol_mapping[last_received_status]
        services_output += f" {text_color_mapping[last_received_status]}{service_name}{RESET}"

    request_string = f'{request_id[:4]}..{request_id[-4:]}'
    combined_output = f'[{request_string}] [{"".join(status_indicators)}]{services_output}'

    print(combined_output)


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

