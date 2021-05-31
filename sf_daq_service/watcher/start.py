import argparse
import logging

from sf_daq_service.watcher.status_recorder import StatusRecorder
from sf_daq_service.common import broker_config
from sf_daq_service.common.broker_client import BrokerClient

_logger = logging.getLogger("BrokerListenerConsoleClient")

RESET = u"\u001b[0m"

GREEN_TEXT = u'\u001b[32m'
YELLOW_TEXT = u'\u001b[33m'
RED_TEXT = u'\u001b[31m'
BLACK_TEXT = u'\u001b[30m'

RED_BACKGROUND = u'\u001b[41m'
GREEN_BACKGROUND = u'\u001b[42m'
YELLOW_BACKGROUND = u'\u001b[43m'

status_symbol_mapping = {
    broker_config.ACTION_REQUEST_START: BLACK_TEXT + YELLOW_BACKGROUND + '*' + RESET,
    broker_config.ACTION_REQUEST_SUCCESS: BLACK_TEXT + GREEN_BACKGROUND + '+' + RESET,
    broker_config.ACTION_REQUEST_FAIL: BLACK_TEXT + RED_BACKGROUND + '-' + RESET
}

text_color_mapping = {
    broker_config.ACTION_REQUEST_START: YELLOW_TEXT,
    broker_config.ACTION_REQUEST_SUCCESS: GREEN_TEXT,
    broker_config.ACTION_REQUEST_FAIL: RED_TEXT
}

service_status_order = {
    broker_config.ACTION_REQUEST_FAIL: 0,
    broker_config.ACTION_REQUEST_START: 1,
    broker_config.ACTION_REQUEST_SUCCESS: 2
}


def print_to_console(request_id, status):

    output_statuses = []
    for service_name, statuses in sorted(status['services'].items()):
        last_received_status = statuses[-1][0]

        status_order = service_status_order[last_received_status]
        indicator_string = status_symbol_mapping[last_received_status]
        name_string = f" {text_color_mapping[last_received_status]}{service_name}{RESET}"

        output_statuses.append((status_order, name_string, indicator_string))
    output_statuses = sorted(output_statuses)

    request_string = f'{request_id[:4]}..{request_id[-4:]}'

    combined_output = f'[{request_string}] ' \
                      f'[{"".join((x[2] for x in output_statuses))}]' \
                      f'{"".join((x[1] for x in output_statuses))}'

    print(combined_output)


def start_console_output(tag, broker_url):
    aggregator = StatusRecorder(on_status_change_function=print_to_console)
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

