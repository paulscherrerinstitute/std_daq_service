import argparse
import json
import logging
from time import sleep

import zmq

from std_daq_service.epics.config import BUFFER_STREAM_URL, STATS_INTERVAL
from std_daq_service.epics.ingestion.receiver import EpicsReceiver
from std_daq_service.epics.ingestion.stats import EpicsIngestionStats

_logger = logging.getLogger("EpicsIngestion")


def start_epics_buffer(service_name, pv_names):
    live_stream_url = BUFFER_STREAM_URL % service_name
    _logger.info(f"Starting live stream on {live_stream_url}.")

    ctx = zmq.Context()
    output_stream = ctx.socket(zmq.PUB)
    output_stream.bind(live_stream_url)

    stats = EpicsIngestionStats()

    def on_pv_event(**kwargs):
        output_stream.send_json(kwargs)
        stats.record(**kwargs)

    EpicsReceiver(pv_names=pv_names, change_callback=on_pv_event)

    try:
        while True:
            sleep(STATS_INTERVAL)
            stats.write_stats()

    except KeyboardInterrupt:
        _logger.info("Received interrupt signal. Exiting.")

    except Exception:
        _logger.error("Epics ingestion service error.")

    finally:
        output_stream.close()


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
    _logger.debug(f"Service started with config: {config}")

    start_epics_buffer(pv_names=config['pv_names'])

    _logger.info(f'Service {args.service_name} stopping.')
