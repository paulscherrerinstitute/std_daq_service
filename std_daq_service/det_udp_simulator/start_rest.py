import argparse
import json
import logging

from flask import Flask, jsonify
from flask_cors import CORS

from std_daq_service.det_udp_simulator.sim import SimulationRestManager
from std_daq_service.rest_v2.utils import validate_config

_logger = logging.getLogger("DetectorSimulator")
request_logger = logging.getLogger('request_log')

STATUS_ENDPOINT = '/status'
START_ENDPOINT = '/start'
STOP_ENDPOINT = '/stop'

def start_api(config_file, rest_port, ansible_repo_folder):
    sim_manager = None

    try:
        with open(config_file, 'r') as input_file:
            daq_config = json.load(input_file)
        validate_config(daq_config)

        detector_name = daq_config['detector_name']

        _logger.info(f'Starting Udp Simulator for detector_name={detector_name} (rest_port={rest_port}).')

        app = Flask(__name__, static_folder='static')
        CORS(app)

        sim_manager = SimulationRestManager(daq_config=daq_config)

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
        app.run(host='0.0.0.0', port=rest_port)

    except Exception as e:
        _logger.exception("Error while trying to run the REST api")

    finally:
        _logger.info("Starting shutdown procedure.")
        if sim_manager:
            sim_manager.close()

    _logger.info("Udp simulator properly shut down.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Standard DAQ Detector simulator')
    parser.add_argument("config_file", type=str, help="Path to JSON config file.")
    parser.add_argument("--rest_port", type=int, help="Port for REST api", default=5000)

    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)

    start_api(config_file=args.config_file, rest_port=args.rest_port)
