import argparse
import logging

import zmq
from flask import Flask

from std_daq_service.interface.config.ansible import AnsibleConfigDriver
from std_daq_service.writer_driver.start_stop import WriterDriver
from std_daq_service.rest_v2.manager import StartStopRestManager
from std_daq_service.rest_v2.rest import register_rest_interface
from std_daq_service.writer_driver.utils import get_stream_addresses, generate_mjpg_image_stream

_logger = logging.getLogger(__name__)


def start_api(beamline_name, detector_name, rest_port):
    _logger.info(f'Starting Start Stop REST for detector_name={detector_name} on beamline_name={beamline_name} '
                 f'(rest_port={rest_port}).')

    command_address, in_status_address, out_status_address, image_metadata_address = get_stream_addresses(detector_name)

    app = Flask(detector_name, template_folder='static/')
    ctx = zmq.Context()

    writer_driver = WriterDriver(ctx, command_address, in_status_address, out_status_address, image_metadata_address)
    config_driver = AnsibleConfigDriver()
    rest_manager = StartStopRestManager(ctx, writer_driver, config_driver)

    register_rest_interface(app, rest_manager, generate_mjpg_image_stream)

    try:
        app.run(host='0.0.0.0', port=rest_port)
    finally:
        _logger.info("Starting shutdown procedure.")

        rest_manager.close()
        writer_driver.close()
        config_driver.close()

    _logger.info("Start Stop REST properly shut down.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Standard DAQ Start Stop REST interface')
    parser.add_argument("beamline_name", type=str, help="Beamline on which this instance is running.")
    parser.add_argument("detector_name", type=str, help="Name of the detector to write.")
    parser.add_argument("--rest_port", type=int, help="Port for REST api", default=5000)

    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)

    start_api(beamline_name=args.beamline_name,
              detector_name=args.detector_name,
              rest_port=args.rest_port)
