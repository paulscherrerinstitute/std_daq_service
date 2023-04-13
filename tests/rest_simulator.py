import argparse
import copy
import logging
import json
import os
import re
from collections import deque

from time import time, sleep
from flask import Flask, request, jsonify, make_response
from threading import Thread, Event

from flask_cors import CORS

_logger = logging.getLogger("StartStopWriterRestInterface")


def extract_write_parameters_from_request(json_request):
    if 'output_file' not in json_request:
        raise RuntimeError(f'Mandatory field missing: output_file')
    output_file = json_request['output_file']

    if not output_file.startswith('/'):
        raise RuntimeError(f'Invalid output_file={output_file}. Path must be absolute - starts with "/".')

    path_validator = '\/[a-zA-Z0-9_\/-]*\..+[^\/]$'
    if not re.compile(path_validator).match(output_file):
        raise RuntimeError(f'Invalid output_file={output_file}. Must be a valid posix path.')

    path_folder = os.path.dirname(output_file)
    if not os.path.exists(path_folder):
        raise RuntimeError(f'Output file folder {path_folder} does not exist. Please create it first.')

    if 'n_images' not in json_request:
        raise RuntimeError(f'Mandatory field missing: n_images')

    try:
        n_images_str = json_request['n_images']
        n_images = int(n_images_str)
    except:
        raise RuntimeError(f'Cannot convert n_images={n_images_str} to an integer. Must be an integer >= 1.')

    if n_images < 1:
        raise RuntimeError(f'Invalid n_images={n_images}. Must be an integer >= 1.')

    return output_file, n_images


class StartStopRestManager(object):
    def __init__(self, ctx, detector_name):
        image_metadata_stream = f'{detector_name}-image'
        writer_control_stream = f'{detector_name}-writer'
        writer_status_stream = f'{detector_name}-writer-status'
        _logger.info(f'Writing stream {image_metadata_stream} to {writer_control_stream}.')

        self.stop_event = Event()
        self.sim_thread = Thread(target=self._sim_async)

        self.writer_state = {'state': 'READY',
                             'acquisition': {
                                 'state': 'FINISHED',
                                 'info': {},
                                 'stats': {}
                             }}

        self.daq_config = {
          "detector_name": "Eiger9M",
          "detector_type": "eiger",
          "n_modules": 72,
          "bit_depth": 32,
          "image_pixel_height": 2016,
          "image_pixel_width": 2016,
          "start_udp_port": 2000
        }

        self.statistics = {
            "bytes_per_second": 12345678,
            "images_per_second": 1500
        }

        self.logs = deque(maxlen=50)

        self.deployment = {
            'status': 'SUCCESS',
            'deployment_id': '1234',
            'stats': {'start_time': time() - 5, 'stop_time': time()}
        }

    def write_sync(self, output_file, n_images):
        if self.writer_state['state'] != "READY":
            raise RuntimeError('Cannot start writing until writer state is READY. '
                               'Stop the current acquisition or wait for it to finish.')

        self.writer_state = {'state': 'READY',
                             'acquisition': {
                                 'info': {'n_images': n_images, 'output_file': output_file},
                                 'state': "FINISHED",
                                 'message': 'Completed successfully',
                                 'stats': {'start_time': time(),
                                           'stop_time': time()+2,
                                           'n_write_requested': n_images,
                                           'n_write_completed': n_images}
                             }}
        sleep(min(5, n_images-1))
        return self.get_status()

    def _sim_async(self):
        n_images = self.writer_state['acquisition']['info']['n_images']

        for i in range(n_images):
            sleep(0.1)

            if self.stop_event.is_set():
                self.writer_state['acquisition']['message'] = 'Interrupted'
                break

            self.writer_state['acquisition']['state'] = 'ACQUIRING_IMAGES'
            self.writer_state['acquisition']['stats']['n_write_requested'] = i + 1
            self.writer_state['acquisition']['stats']['n_write_completed'] = i

        else:
            self.writer_state['acquisition']['message'] = 'Completed'

        self.writer_state['acquisition']['state'] = 'FLUSHING_IMAGES'
        sleep(2)

        self.writer_state['acquisition']['state'] = 'FINISHED'
        self.writer_state['acquisition']['stats']['stop_time'] = time()
        self.writer_state['acquisition']['stats']['n_write_completed'] = \
        self.writer_state['acquisition']['stats']['n_write_requested']
        self.writer_state['state'] = 'READY'

        self.logs.append(copy.deepcopy(self.writer_state['acquisition']))

    def write_async(self, output_file, n_images):
        if self.writer_state['state'] != "READY":
            raise RuntimeError('Cannot start writing until writer state is READY. '
                               'Stop the current acquisition or wait for it to finish.')

        self.writer_state = {'state': 'WRITING',
                             'acquisition': {
                                 'info': {'n_images': n_images, 'output_file': output_file},
                                 'state': "WAITING_IMAGES",
                                 'stats': {'start_time': time(),
                                           'stop_time': None,
                                           'n_write_requested': 0,
                                           'n_write_completed': 0}
                             }}

        self.stop_event.clear()
        self.sim_thread = Thread(target=self._sim_async)
        self.sim_thread.start()

        return self.get_status()

    def stop_writing(self):
        self.stop_event.set()
        self.sim_thread.join()

        return self.get_status()

    def get_status(self):
        return self.writer_state

    def close(self):
        _logger.info("Shutting down manager.")
        self.driver.close()


def start_rest_api(detector_name, rest_port):
    app = Flask(detector_name)
    CORS(app)
    ctx = None
    manager = StartStopRestManager(ctx=ctx, detector_name=detector_name)

    @app.route("/write_sync", methods=['POST'])
    def write_sync_request():
        json_request = request.json
        output_file, n_images = extract_write_parameters_from_request(json_request)

        writer_status = manager.write_sync(output_file, n_images)

        return jsonify({"status": "ok",
                        "message": "Writing finished.",
                        'writer': writer_status})

    @app.route('/write_async', methods=['POST'])
    def write_async_request():
        json_request = request.json
        output_file, n_images = extract_write_parameters_from_request(json_request)

        writer_status = manager.write_async(output_file, n_images)

        return jsonify({"status": "ok",
                        "message": "Writing started.",
                        'writer': writer_status})

    @app.route('/status', methods=['GET'])
    def get_status_request():
        writer_status = manager.get_status()

        return jsonify({"status": "ok",
                        "message": f"Writer is {writer_status['state']}",
                        'writer': writer_status})

    @app.route('/stop', methods=['POST'])
    def stop_writing_request():
        writer_status = manager.stop_writing()

        return jsonify({"status": "ok",
                        "message": "Writing stopped.",
                        'writer': writer_status})


    @app.route('/config', methods=['GET'])
    def get_config_request():
        bit_depth = manager.daq_config['bit_depth']
        return jsonify({"status": "ok",
                        "message": f"DAQ configured for bit_depth={bit_depth}.",
                        'config': manager.daq_config})

    @app.route('/stats', methods=['GET'])
    def get_statistics():
        return jsonify({"status": "ok",
                        "message": f"DAQ statistics for {detector_name}.",
                        'stats': manager.statistics})

    @app.route('/logs/<int:n_logs>', methods=['GET'])
    def get_logs(n_logs):
        return jsonify({"status": "ok",
                        "message": f"DAQ logs for {detector_name}.",
                        'logs': list(manager.logs)[-n_logs:]})
    @app.route('/deployment', methods=['GET'])
    def get_deployment_status():

        return jsonify({"status": "ok",
                        "message": f"Deployment for {detector_name}.",
                        'deployment': manager.deployment})

    @app.route('/config', methods=['POST'])
    def set_config_request():
        change_request = request.json

        new_config = dict(manager.daq_config)
        new_config.update(change_request)

        valid_fields = ['bit_depth', 'detector_name', 'detector_type', 'image_pixel_height',
                        'image_pixel_width', 'n_modules', 'start_udp_port']
        new_config = {k: new_config[k] for k in valid_fields}

        if new_config['bit_depth'] not in [4, 8, 16, 32]:
            raise ValueError(f"Invalid bit_depth={new_config['bit_depth']}. Valid values: 4, 8, 16, 32")

        if new_config['detector_type'] not in ['eiger', 'gigafrost', 'jungfrau']:
            raise ValueError(f"Invalid detector_type={new_config['detector_type']}. Valid values: "
                             f"eiger, gigafrost, jungfrau")

        sleep(5)

        bit_depth = new_config['bit_depth']

        manager.daq_config = new_config

        return jsonify({"status": "ok",
                        "message": f"DAQ configured for bit_depth={bit_depth}.",
                        'config': manager.daq_config})

    @app.errorhandler(Exception)
    def error_handler(e):
        _logger.exception(e)
        return jsonify({'status': 'error',
                        'message': str(e)}), 200

    try:
        app.run(host='0.0.0.0', port=rest_port)
    finally:
        manager.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='StartStop Writer REST interface')
    parser.add_argument("--rest_port", type=int, help="Port for REST api", default=5000)

    args = parser.parse_args()
    detector_name = 'simulation'
    rest_port = args.rest_port

    logging.basicConfig(level=logging.INFO)

    _logger.info(f'Starting StartStop writer REST interface for {detector_name} on {rest_port}.')

    start_rest_api(detector_name, rest_port)

    _logger.info(f'Service {args.service_name} stopped.')
