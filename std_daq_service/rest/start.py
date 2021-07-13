import argparse
import logging

from flask import Flask, request, jsonify

from std_daq_service.broker.client import BrokerClient
from std_daq_service.broker.common import TEST_BROKER_URL
from std_daq_service.broker.status_aggregator import StatusAggregator
from std_daq_service.rest.eiger import set_eiger_config, get_eiger_config
from std_daq_service.rest.manager import RestManager
from std_daq_service.rest.request_factory import build_user_response, extract_write_request

_logger = logging.getLogger("RestProxyService")


def start_rest_api(service_name, broker_url, tag):
    app = Flask(service_name)
    manager = RestManager(broker_url=broker_url, tag=tag)

    @app.route("/write_sync", methods=['POST'])
    def write_sync_request():
        message = extract_write_request(request.json)

        request_id, broker_response = manager.write_sync(message)

        return jsonify({"request_id": request_id,
                        'response': build_user_response(response=broker_response)})

    @app.route('/write_async', methods=['POST'])
    def write_async_request():
        message = extract_write_request(request.json)

        request_id = manager.write_async(message)

        return jsonify({"request_id": request_id})

    @app.route('/write_kill', methods=['POST'])
    def write_kill():
        kill_request = request.json

        if 'request_id' not in kill_request:
            raise RuntimeError('Mandatory field "request_id" missing.')
        request_id = kill_request['request_id']

        broker_response = manager.kill_sync(request_id)

        return jsonify({'request_id': request_id,
                        'response': build_user_response(response=broker_response)})

    @app.route('/detector/<det_name>', methods=['GET'])
    def get_detector_config(det_name):
        response = get_eiger_config(det_name)

        return jsonify(response)

    @app.route('/detector', methods=['POST'])
    def set_detector_config():
        config = request.json

        response = set_eiger_config(config)
        return jsonify(response)

    app.run(host='127.0.0.1', port=5000)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Rest Proxy Service')

    parser.add_argument("service_name", type=str, help="Name of the service")
    parser.add_argument("tag", type=str, help="Tag on which the proxy listens to statuses and sends requests.")

    parser.add_argument("--broker_url", default=TEST_BROKER_URL,
                        help="Address of the broker to connect to.")
    parser.add_argument("--log_level", default="INFO",
                        choices=['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG'],
                        help="Log level to use.")

    args = parser.parse_args()

    _logger.setLevel(args.log_level)
    logging.getLogger("pika").setLevel(logging.WARNING)

    _logger.info(f'Service {args.service_name} connecting to {args.broker_url}.')
    print(f'Service {args.service_name} connecting to {args.broker_url}.')

    start_rest_api(service_name=args.service_name,
                   broker_url=args.broker_url,
                   tag=args.tag)

    _logger.info(f'Service {args.service_name} stopping.')
