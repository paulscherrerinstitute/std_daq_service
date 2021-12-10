import argparse
import logging
import os

from std_daq_service.epics_buffer.buffer import start_epics_buffer
from std_daq_service.start_utils import default_service_setup

_logger = logging.getLogger("EpicsBuffer")


def main():
    parser = argparse.ArgumentParser(description="Epics buffer service")
    parser.add_argument("--redis_host", type=str, help="Host of redis instance.",
                        default=os.environ.get("REDIS_HOST", "localhost"))
    service_name, config, args = default_service_setup(parser)

    redis_host = args.redis_host

    _logger.info(f'Service {service_name} starting with REDIS_HOST {redis_host}.')
    _logger.debug(config)

    pulse_id_pv = config.get("pulse_id_pv")
    pv_names = config.get('pv_list')

    if not pv_names:
        raise ValueError("Invalid config file. Must set pv_names list.", config)

    start_epics_buffer(service_name=service_name,
                       redis_host=redis_host,
                       pv_names=pv_names,
                       pulse_id_pv=pulse_id_pv)

    _logger.info(f'Service {service_name} stopping.')


if __name__ == "__main__":
    main()
