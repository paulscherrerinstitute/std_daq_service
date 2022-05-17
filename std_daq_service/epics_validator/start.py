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
    start_pulse_id = request["start_pulse_id"]
    stop_pulse_id = request['stop_pulse_id']

    _logger.info(f"Validating request {request_id} file {output_file}.")

    expected_channels = request['channels']
    with h5py.File(output_file, mode='r') as input_file:

        validation_data = []
        for channel in expected_channels:
            if channel not in input_file:
                validation_data.append(f"[{channel}] No data")
                continue

            pulse_id_map = input_file[channel].get('pulse_id', None)
            if pulse_id_map is None:
                validation_data.append(f'[{channel}] Missing pulse_id mapping')
            else:
                n_pulses_before_start = 0
                for pulse_id in pulse_id_map:
                    if pulse_id < start_pulse_id:
                        n_pulses_before_start += 1
                    else:
                        break

                n_pulses_after_end = 0
                for i in range(len(pulse_id_map)-1, -1, -1):
                    pulse_id = pulse_id_map[i]

                    if pulse_id >= stop_pulse_id:
                        n_pulses_after_end += 1
                    else:
                        break

                n_pulses_in_interval = len(pulse_id_map) - n_pulses_before_start - n_pulses_after_end
                validation_data.append(f'[{channel}] Point count {len(pulse_id_map)} '
                                       f'({n_pulses_before_start}[{n_pulses_in_interval}){n_pulses_after_end})')

    return validation_data


def main():
    parser = argparse.ArgumentParser(description='Epics buffer writer service')
    parser.add_argument("primary_service_name", type=str, help="Name of the primary service to listen to")
    parser.add_argument("--broker_url", type=str, help="Host of broker instance.",
                        default=os.environ.get("BROKER_HOST", '127.0.0.1'))

    service_name, config, args = default_service_setup(parser)

    broker_url = args.broker_url
    primary_service_name = args.primary_service_name

    _logger.info(f'Epics validator {service_name} listening on broker {broker_url} '
                 f'for primary service {primary_service_name}.')

    service = EpicsValidationService(file_validator=validate_file, primary_service_name=primary_service_name)
    client = BrokerClient(broker_url=broker_url, tag="#", status_callback=service.on_status_change)

    try:
        client.block()
    except KeyboardInterrupt:
        _logger.info("User interruption request. Ending service.")
    finally:
        client.stop()

    _logger.info(f'Service {args.service_name} stopping.')


if __name__ == "__main__":
    main()
