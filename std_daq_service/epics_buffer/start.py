import argparse
import json
import logging
import struct

import epics
import zmq

from std_daq_service.epics_buffer.buffer import SyncEpicsBuffer
from std_daq_service.epics_buffer.receiver import EpicsReceiver
from std_daq_service.epics_buffer.writer import EpicsBufferWriter

_logger = logging.getLogger("EpicsBuffer")

BUFFER_STREAM_URL = "inproc://buffer_stream"


def start_epics_buffer(sampling_pv, pv_names, buffer_folder):
    buffer = SyncEpicsBuffer(pv_names=pv_names)
    EpicsReceiver(pv_names=pv_names, change_callback=buffer.change_callback)
    writer = EpicsBufferWriter(buffer_folder=buffer_folder)

    _logger.info(f'Sampling epics buffer with {sampling_pv} and writing to {buffer_folder}.')
    _logger.debug(f'Connecting to PVs: {pv_names}')

    ctx = zmq.Context()
    output_stream = ctx.socket(zmq.PUB)
    output_stream.bind(BUFFER_STREAM_URL)

    input_stream = ctx.socket(zmq.SUB)
    input_stream.setsockopt(zmq.RCVTIMEO, 100)
    input_stream.connect(BUFFER_STREAM_URL)
    input_stream.setsockopt_string(zmq.SUBSCRIBE, "")

    def on_sampling_pv(value, **kwargs):
        output_stream.send(struct.pack('<Q', int(value)), flags=zmq.SNDMORE)
        output_stream.send_json(buffer.cache)

    epics.PV(pvname=sampling_pv, callback=on_sampling_pv, form='time', auto_monitor=True)

    try:
        while True:
            try:
                pulse_id_bytes, data = input_stream.recv_multipart()
            except zmq.Again:
                continue

            writer.write(pulse_id_bytes, data)

    except KeyboardInterrupt:
        _logger.info("Received interrupt signal. Exiting.")

    except Exception:
        _logger.error("Epics buffer error.")

    finally:
        writer.close()
        output_stream.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Epics buffer receiver')

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

    start_epics_buffer(sampling_pv=config["sampling_pv"],
                       pv_names=config['pv_names'],
                       buffer_folder=config['buffer_folder'])

    _logger.info(f'Service {args.service_name} stopping.')
