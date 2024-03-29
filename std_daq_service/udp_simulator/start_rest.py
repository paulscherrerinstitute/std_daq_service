import argparse
import json
import logging

from flask import Flask, jsonify
from flask_cors import CORS

from std_daq_service.config import validate_config
from std_daq_service.udp_simulator.sim import SimulationRestManager

_logger = logging.getLogger("DetectorSimulator")
request_logger = logging.getLogger('request_log')

STATUS_ENDPOINT = '/status'
START_ENDPOINT = '/start'
STOP_ENDPOINT = '/stop'


def start_api(config_file, rest_port, image_filename, output_ip):
    sim_manager = None

    try:
        with open(config_file, 'r') as input_file:
            daq_config = json.load(input_file)
        validate_config(daq_config)

        detector_name = daq_config['detector_name']

        _logger.info(f'Starting Udp Simulator for detector_name={detector_name} (rest_port={rest_port}).')

        app = Flask(__name__, static_folder='static')
        CORS(app)

        sim_manager = SimulationRestManager(daq_config=daq_config, output_ip=output_ip, image_filename=image_filename)

        @app.route(STATUS_ENDPOINT)
        def get_status_request():
            status = sim_manager.get_status()
            return jsonify({"status": "ok",
                            "message": f"Simulator for {detector_name}.",
                            'simulator': status})

        @app.route(START_ENDPOINT, methods=['POST'])
        def start_request():
            request_logger.info(f'Start simulation')
            sim_manager.start()
            return get_status_request()

        @app.route(STOP_ENDPOINT, methods=['POST'])
        def stop_request():
            request_logger.info(f'Stop simulation')
            sim_manager.stop()
            return get_status_request()

        log = logging.getLogger('werkzeug')
        log.setLevel(logging.ERROR)
        app.run(host='0.0.0.0', port=rest_port, threaded=True)

    except Exception as e:
        _logger.exception("Error while trying to run the REST api")

    finally:
        _logger.info("Starting shutdown procedure.")
        if sim_manager:
            sim_manager.close()

    _logger.info("Udp simulator properly shut down.")

def main():
    parser = argparse.ArgumentParser(description='Standard DAQ Detector simulator')
    parser.add_argument("config_file", type=str, help="Path to JSON config file.")
    parser.add_argument('output_ip', type=str, help='IP to send the UPD packets to.')
    parser.add_argument("--rest_port", type=int, help="Port for REST api", default=5001)
    parser.add_argument('-f', '--file', type=str, default=None, help='Image in TIFF format to stream.')

    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)

    start_api(config_file=args.config_file, rest_port=args.rest_port, image_filename=args.file,
              output_ip=args.output_ip)

if __name__ == "__main__":
    main()
