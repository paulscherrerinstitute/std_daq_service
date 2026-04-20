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
    parser.add_argument("--broker_username", type=str, help="User name for broker authentication",
                        default=os.environ.get("BROKER_USERNAME"))
    parser.add_argument("--broker_password", type=str, help="Password for broker authentication",
                        default=os.environ.get("BROKER_PASSWORD"))

    args = parser.parse_args()

    # Suppress pika logging
    logging.getLogger("pika").setLevel(logging.WARNING)

    request_file = args.request_json
    broker_url = args.broker_url
    broker_username = args.broker_username
    broker_password = args.broker_password
    tag = args.tag

    with open(request_file, 'r') as input_file:
        request_json = json.load(input_file)

    client = BrokerClient(broker_url=broker_url, username=broker_username, password=broker_password, tag=tag)
    client.send_request(request_json)
    client.stop()


if __name__ == "__main__":
    main()
