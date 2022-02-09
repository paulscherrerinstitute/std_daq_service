import argparse
import logging
import os

import h5py

from std_daq_service.broker.client import BrokerClient
from std_daq_service.epics_validator.service import EpicsValidationService
from std_daq_service.start_utils import default_service_setup

_logger = logging.getLogger("EpicsWriter")


def validate_file(request_id, request):
    output_file = request['output_file']
    _logger.info(f"Validating request {request_id} file {output_file}.")

    expected_channels = request['channels']
    with h5py.File(output_file, mode='r') as input_file:

        missing_channels = []
        for channel in expected_channels:
            if channel not in input_file:
                missing_channels.append(f"Missing pv {channel}")

    return missing_channels


def main():
    parser = argparse.ArgumentParser(description='Epics buffer writer service')
    parser.add_argument("--broker_url", type=str, help="Host of broker instance.",
                        default=os.environ.get("BROKER_HOST", '127.0.0.1'))
    parser.add_argument("--tag", type=str, help="Tag to listen for on the broker",
                        default="#")

    service_name, config, args = default_service_setup(parser)

    broker_url = args.broker_url
    primary_tag = args.tag

    _logger.info(f'Epics validator {service_name} listening on broker {broker_url} '
                 f'for primary service {primary_tag}.')

    service = EpicsValidationService(file_validator=validate_file)
    client = BrokerClient(broker_url=broker_url, tag=primary_tag, status_callback=service.on_status_change)

    try:
        client.block()
    except KeyboardInterrupt:
        _logger.info("User interruption request. Ending service.")
    finally:
        client.stop()

    _logger.info(f'Service {args.service_name} stopping.')


if __name__ == "__main__":
    main()
