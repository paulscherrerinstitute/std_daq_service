import argparse
import json
import logging

import zmq
from flask import Flask


from std_daq_service.rest_v2.daq import DaqRestManager, AnsibleConfigDriver
from std_daq_service.rest_v2.simulation import SimulationRestManager
from std_daq_service.rest_v2.stats import ImageMetadataStatsDriver
from std_daq_service.rest_v2.utils import validate_config
from std_daq_service.writer_driver.start_stop_driver import WriterDriver
from std_daq_service.rest_v2.writer import WriterRestManager
from std_daq_service.rest_v2.rest import register_rest_interface
from std_daq_service.writer_driver.utils import get_stream_addresses
from flask_cors import CORS

_logger = logging.getLogger(__name__)


def start_api(beamline_name, daq_config, rest_port):
    detector_name = daq_config['detector_name']

    _logger.info(f'Starting Start Stop REST for detector_name={detector_name} on beamline_name={beamline_name} '
                 f'(rest_port={rest_port}).')

    command_address, in_status_address, out_status_address, image_metadata_address = get_stream_addresses(detector_name)

    app = Flask(detector_name, static_folder='static')
    CORS(app)
    ctx = zmq.Context()

    writer_driver = WriterDriver(ctx, command_address, in_status_address, out_status_address, image_metadata_address)
    writer_manager = WriterRestManager(writer_driver=writer_driver)

    stats_driver = ImageMetadataStatsDriver(ctx, image_metadata_address)
    config_driver = AnsibleConfigDriver()
    daq_manager = DaqRestManager(stats_driver=stats_driver, config_driver=config_driver, writer_driver=writer_driver)

    sim_manager = SimulationRestManager(daq_config=daq_config)

    register_rest_interface(app, writer_manager=writer_manager, daq_manager=daq_manager, sim_manager=sim_manager)

    try:
        log = logging.getLogger('werkzeug')
        log.setLevel(logging.ERROR)
        app.run(host='0.0.0.0', port=rest_port)
    finally:
        _logger.info("Starting shutdown procedure.")

        daq_manager.close()
        sim_manager.close()
        writer_manager.close()

    _logger.info("Start Stop REST properly shut down.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Standard DAQ Start Stop REST interface')
    parser.add_argument("beamline_name", type=str, help="Beamline on which this instance is running.")
    parser.add_argument("config_file", type=str, help="Path to JSON config file.")
    parser.add_argument("--rest_port", type=int, help="Port for REST api", default=5000)

    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)

    with open(args.config_file, 'r') as input_file:
        config = json.load(input_file)

    validate_config(config)

    start_api(beamline_name=args.beamline_name,
              daq_config=config,
              rest_port=args.rest_port)
