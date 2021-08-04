import argparse
import json
import logging

_logger = logging.getLogger("EpicsBuffer")


def start_epics_buffer(config):
    pass


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Epics buffer receiver')

    parser.add_argument("service_name", type=str, help="Name of the service")
    parser.add_argument("pv_list", type=str, help="Path to the json config file.")

    parser.add_argument("--log_level", default="INFO",
                        choices=['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG'],
                        help="Log level to use.")

    args = parser.parse_args()

    _logger.setLevel(args.log_level)

    _logger.info(f'Service {args.service_name} starting.')

    with open(args.json_config_file, 'r') as input_file:
        config = json.load(input_file)

    start_epics_buffer(config)

    _logger.info(f'Service {args.service_name} stopping.')
