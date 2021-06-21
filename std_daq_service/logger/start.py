import argparse
import logging

from std_daq_service.broker.client import BrokerClient
from std_daq_service.broker.common import ACTION_REQUEST_START, ACTION_REQUEST_SUCCESS, ACTION_REQUEST_FAIL, \
    TEST_BROKER_URL
from std_daq_service.logger.status_recorder import StatusRecorder

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
    ACTION_REQUEST_START: BLACK_TEXT + YELLOW_BACKGROUND + '*' + RESET,
    ACTION_REQUEST_SUCCESS: BLACK_TEXT + GREEN_BACKGROUND + '+' + RESET,
    ACTION_REQUEST_FAIL: BLACK_TEXT + RED_BACKGROUND + '-' + RESET
}

text_color_mapping = {
    ACTION_REQUEST_START: YELLOW_TEXT,
    ACTION_REQUEST_SUCCESS: GREEN_TEXT,
    ACTION_REQUEST_FAIL: RED_TEXT
}

service_status_order = {
    ACTION_REQUEST_FAIL: 0,
    ACTION_REQUEST_START: 1,
    ACTION_REQUEST_SUCCESS: 2
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
    print("WTF")
    recorder = StatusRecorder(on_status_change_function=print_to_console)

    client = BrokerClient(broker_url=broker_url, tag=tag, status_callback=recorder.on_status_message)
    client.block()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Broker logger')

    parser.add_argument("tag", type=str, default="#", help="Tag to bind to on the status exchange.")
    parser.add_argument("--broker_url", default=TEST_BROKER_URL,
                        help="Address of the broker to connect to.")
    parser.add_argument("--log_level", default="ERROR",
                        choices=['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG'],
                        help="Log level to use.")

    args = parser.parse_args()

    _logger.setLevel(args.log_level)
    logging.getLogger("pika").setLevel(logging.WARNING)

    start_console_output(tag=args.tag, broker_url=args.broker_url)
