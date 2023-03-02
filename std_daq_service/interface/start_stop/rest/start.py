import argparse
import logging

from flask import Flask

from std_daq_service.interface.start_stop.rest.manager import StartStopRestManager
from std_daq_service.interface.start_stop.rest.rest import register_rest_interface
from std_daq_service.interface.start_stop.utils import get_stream_addresses

_logger = logging.getLogger(__name__)


def start_api(beamline_name, detector_name, rest_port):
    _logger.info(f'Starting Start Stop REST for detector_name={detector_name} on beamline_name={beamline_name} '
                 f'(rest_port={rest_port}).')

    image_metadata_stream, writer_control_stream, writer_status_stream = get_stream_addresses(detector_name)


    app = Flask(detector_name)
    ctx = None
    writer_driver = None
    config_driver = None
    rest_manager = StartStopRestManager(ctx, writer_driver, config_driver)

    register_rest_interface(app, rest_manager)

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
