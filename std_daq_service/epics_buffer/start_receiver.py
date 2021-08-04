import argparse
import json
import logging
import signal

import epics
import zmq

from std_daq_service.epics_buffer.buffer import SyncEpicsBuffer
from std_daq_service.epics_buffer.receiver import EpicsReceiver

_logger = logging.getLogger("EpicsBuffer")


def start_epics_buffer(sampling_pv, pv_names, output_stream_url):
    buffer = SyncEpicsBuffer(pv_names=pv_names)
    EpicsReceiver(pv_names=pv_names, change_callback=buffer.change_callback)

    ctx = zmq.Context()

    _logger.info(f'Binding output stream to {output_stream_url}.')
    output_stream = ctx.socket(zmq.PUB)
    output_stream.bind(output_stream_url)

    def on_sampling_pv(value, **kwargs):
        output_stream.send(value, flags=zmq.SNDMORE)
        output_stream.send(buffer.cache)

    epics.PV(pvname=sampling_pv, callback=on_sampling_pv, form='time', auto_monitor=True)

    try:
       signal.pause()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Epics buffer receiver')

    parser.add_argument("service_name", type=str, help="Name of the service")
    parser.add_argument("sampling_pv", type=str, help="PV used for sampling the Epics buffer")
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
