import argparse
import json
import logging

from std_daq_service.epics_buffer.buffer import start_epics_buffer

DEFAULT_REDIS_HOST = "localhost"

_logger = logging.getLogger("EpicsBuffer")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Epics buffer receiver')

    parser.add_argument("service_name", type=str, help="Name of the service")
    parser.add_argument("json_config_file", type=str, help="Path to JSON config file.")
    parser.add_argument("--redis_host", type=str, help="Host of redis instance.", default=DEFAULT_REDIS_HOST)

    parser.add_argument("--log_level", default="INFO",
                        choices=['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG'],
                        help="Log level to use.")

    args = parser.parse_args()

    _logger.setLevel(args.log_level)

    _logger.info(f'Service {args.service_name} starting.')

    with open(args.json_config_file, 'r') as input_file:
        config = json.load(input_file)
    _logger.debug(config)

    redis_host = args.redis_host
    pulse_id_pv = config.get("pulse_id_pv")
    pv_names = config.get('pv_names')

    if not pv_names:
        raise ValueError("Invalid config file. Must set pv_names list.", config)

    start_epics_buffer(redis_host=redis_host,
                       pv_names=pv_names,
                       pulse_id_pv=pulse_id_pv)

    _logger.info(f'Service {args.service_name} stopping.')
