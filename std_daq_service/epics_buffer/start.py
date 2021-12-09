import logging

from std_daq_service.epics_buffer.buffer import start_epics_buffer
from std_daq_service.start_utils import read_service_arguments

_logger = logging.getLogger("EpicsBuffer")


def main():
    service_name, config, redis_host = read_service_arguments("Epics buffer service")

    _logger.info(f'Service {service_name} starting.')
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
