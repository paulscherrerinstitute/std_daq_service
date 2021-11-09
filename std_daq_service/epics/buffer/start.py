import argparse
import json
import logging
import struct

import epics
import zmq

from std_daq_service.epics.buffer.buffer import SyncEpicsBuffer
from std_daq_service.epics.config import BUFFER_STREAM_URL
from std_daq_service.epics.ingestion.receiver import EpicsReceiver
from std_daq_service.epics.buffer.writer import EpicsBufferWriter

_logger = logging.getLogger("EpicsIngestion")


def start_epics_ingestion(service_name, pv_names):

    _logger.info("Starting epics ingestion service.")
    _logger.debug(f'Connecting to PVs: {pv_names}')

    ctx = zmq.Context()
    output_stream = ctx.socket(zmq.PUB)
    output_stream.bind(BUFFER_STREAM_URL % service_name)

    def on_value_change(value, **kwargs):
        output_stream.send_json(kwargs)

    EpicsReceiver(pv_names=pv_names, change_callback=on_value_change)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Epics ingestion service')

    parser.add_argument("service_name", type=str, help="Name of the service")
    parser.add_argument("json_config_file", type=str, help="Path to JSON config file.")

    parser.add_argument("--log_level", default="INFO",
                        choices=['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG'],
                        help="Log level to use.")

    args = parser.parse_args()

    _logger.setLevel(args.log_level)

    _logger.info(f'Service {args.service_name} starting.')

    with open(args.json_config_file, 'r') as input_file:
        config = json.load(input_file)

    sampling_pv = config["sampling_pv"]
    pv_names = config['pv_names']
    buffer_folder = config['buffer_folder']

    if not sampling_pv or not pv_names or not buffer_folder:
        raise ValueError("Invalid config file. Must set sampling_pv, pv_names and buffer_folder.", config)

    start_epics_buffer(sampling_pv=sampling_pv,
                       pv_names=pv_names,
                       buffer_folder=buffer_folder)

    _logger.info(f'Service {args.service_name} stopping.')
