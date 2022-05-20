import argparse
import logging
import json

from flask import Flask, request, jsonify, make_response

from std_daq_service.broker.common import TEST_BROKER_URL
from std_daq_service.rest.eiger import set_eiger_config, get_eiger_config, set_eiger_cmd, get_eiger_status
from std_daq_service.rest.manager import RestManager
from std_daq_service.rest.request_factory import build_user_response, extract_write_request
from std_daq_service.start_utils import default_service_setup

_logger = logging.getLogger("RestProxyService")


def start_rest_api(service_name, broker_url, tag, config_file):
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
        if det_name.upper() == "EIGER":
            response = get_eiger_config(det_name)

        return jsonify(response)

    @app.route('/detector/<det_name>', methods=['POST'])
    def set_detector_method(det_name):
        if det_name.upper() == "EIGER":
            config_new = request.json
            response={}
            if 'config' in config_new:
                response = make_response(jsonify(set_eiger_config(config_new, config_file)),200,)
            if 'cmd' in config_new:
                if config_new['cmd'].upper() in ['STOP', 'START', 'SET_CONFIG']:
                    response = make_response(jsonify(set_eiger_cmd(config_new['cmd'].upper())),200,)
                elif config_new['cmd'].upper() == 'STATUS':
                    response = make_response(jsonify(get_eiger_status()),200,)
                else:
                    response = make_response(jsonify({'response':'Eiger command not found.'}),200,)
            
            response.headers["Content-Type"] = "application/json"
            return response

    app.run(host='0.0.0.0', port=5000)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='SLS Rest Service')
    parser.add_argument("tag", type=str, help="Tag on which the proxy listens to statuses and sends requests.")
    parser.add_argument("--broker_url", default=TEST_BROKER_URL,
                        help="Address of the broker to connect to.")

    service_name, config, args = default_service_setup(parser)
    broker_url = args.broker_url
    tag = args.tag

    _logger.info(f'Service {service_name} connecting to {broker_url}.')

    start_rest_api(service_name=service_name,
                   broker_url=args.broker_url,
                   tag=args.tag,
                   config_file=args.json_config_file)

    _logger.info(f'Service {args.service_name} stopping.')
