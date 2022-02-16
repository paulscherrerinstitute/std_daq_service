import argparse
import logging
import os

from std_daq_service.broker.client import BrokerClient
from std_daq_service.broker.common import ACTION_REQUEST_START, ACTION_REQUEST_SUCCESS, ACTION_REQUEST_FAIL
from std_daq_service.broker.status_aggregator import StatusAggregator

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


def print_to_console_agg(request_id, status):
    output_statuses = []
    for service_name, statuses in sorted(status['services'].items()):
        last_received_status = statuses[-1][0]

        status_order = service_status_order[last_received_status]
        indicator_string = status_symbol_mapping[last_received_status]
        name_string = f" {text_color_mapping[last_received_status]}{service_name}{RESET}"
        # TODO: Add messages and maybe separate the output to each service individually.

        output_statuses.append((status_order, name_string, indicator_string))

    output_statuses = sorted(output_statuses)

    request_string = f'{request_id[:4]}..{request_id[-4:]}'

    combined_output = f'[{request_string}] ' \
                      f'[{"".join((x[2] for x in output_statuses))}]' \
                      f'{"".join((x[1] for x in output_statuses))}'

    print(combined_output)


def print_to_console_raw(request_id, request, header):
    request_string = f'{request_id[:4]}..{request_id[-4:]}'
    service_name = header['source']
    action = header['action']
    error_message = header['message']
    output_file = request.get("output_file", "")

    if action == ACTION_REQUEST_FAIL:
        output_message = error_message
    else:
        output_message = output_file

    combined_output = f'[{request_string}] ' \
                      f'{text_color_mapping[action]}{service_name}{RESET} ' \
                      f'{text_color_mapping[action]}{action} ' \
                      f'{output_message}'

    print(combined_output)


def main():
    parser = argparse.ArgumentParser(description='Monitor status queue on broker.')
    parser.add_argument("--agg", action="store_true", help="Aggregate status reporting.")
    parser.add_argument("--broker_url", type=str, help="Host of broker instance.",
                        default=os.environ.get("BROKER_HOST", '127.0.0.1'))
    parser.add_argument("--tag", type=str, help="Tag on which to send the request.", default="#")

    args = parser.parse_args()

    broker_url = args.broker_url
    tag = args.tag
    aggregate_output = args.agg

    # Suppress pika logging
    logging.getLogger("pika").setLevel(logging.WARNING)

    if aggregate_output:
        recorder = StatusAggregator(status_change_callback=print_to_console_agg)
        f_on_status_message = recorder.on_status_message
    else:
        f_on_status_message = print_to_console_raw

    client = BrokerClient(broker_url=broker_url, tag=tag, status_callback=f_on_status_message)

    print("Connected. Waiting for messages.")

    try:
        client.block()
    except KeyboardInterrupt:
        client.stop()


if __name__ == "__main__":
    main()
