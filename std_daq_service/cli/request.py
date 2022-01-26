import argparse
import json
import logging
import os

from std_daq_service.broker.client import BrokerClient


def main():
    parser = argparse.ArgumentParser(description='Generate request to broker')
    parser.add_argument("tag", type=str, help="Tag on which to send the request.")
    parser.add_argument("request_json", type=str, help="File with request JSON file to send.")
    parser.add_argument("--broker_url", type=str, help="Host of broker instance.",
                        default=os.environ.get("BROKER_HOST", '127.0.0.1'))

    args = parser.parse_args()

    # Suppress pika logging
    logging.getLogger("pika").setLevel(logging.WARNING)

    request_file = args.request_json
    broker_url = args.broker_url
    tag = args.tag

    with open(request_file, 'r') as input_file:
        request_json = json.load(input_file)

    client = BrokerClient(broker_url=broker_url, tag=tag)
    client.send_request(request_json)
    client.stop()


if __name__ == "__main__":
    main()
