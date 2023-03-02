from flask import request, jsonify

from std_daq_service.interface.start_stop.rest.utils import get_parameters_from_write_request

WRITE_SYNC_ENDPOINT = "/write_sync"
WRITE_ASYNC_ENDPOINT = "/write_async"
STATUS_ENDPOINT = "/status"
STOP_ENDPOINT = "/stop"
CONFIG_ENDPOINT = '/config'
DAQ_CONFIG_FIELDS = ['bit_depth', 'detector_name', 'detector_type', 'image_pixel_height',
                     'image_pixel_width', 'n_modules', 'start_udp_port']


def register_rest_interface(app, manager):
    @app.route(WRITE_SYNC_ENDPOINT, methods=['POST'])
    def write_sync_request():
        json_request = request.json
        output_file, n_images = get_parameters_from_write_request(json_request)

        writer_status = manager.write_sync(output_file, n_images)

        return jsonify({"status": "ok",
                        "message": "Writing finished.",
                        'writer': writer_status})

    @app.route(WRITE_ASYNC_ENDPOINT, methods=['POST'])
    def write_async_request():
        json_request = request.json
        output_file, n_images = get_parameters_from_write_request(json_request)

        writer_status = manager.write_async(output_file, n_images)

        return jsonify({"status": "ok",
                        "message": "Writing started.",
                        'writer': writer_status})

    @app.route(STATUS_ENDPOINT, methods=['GET'])
    def get_status_request():
        writer_status = manager.get_status()

        return jsonify({"status": "ok",
                        "message": f"Writer is {writer_status['state']}",
                        'writer': writer_status})

    @app.route(STOP_ENDPOINT, methods=['POST'])
    def stop_writing_request():
        writer_status = manager.stop_writing()

        return jsonify({"status": "ok",
                        "message": "Writing stopped.",
                        'writer': writer_status})

    @app.route(CONFIG_ENDPOINT, methods=['GET'])
    def get_config_request():
        daq_config = manager.get_config()
        return jsonify({"status": "ok",
                        "message": f"DAQ configured for bit_depth={daq_config['bit_depth']}.",
                        'config': manager.daq_config})

    @app.route(CONFIG_ENDPOINT, methods=['POST'])
    def set_config_request():
        config_change_request = request.json
        daq_config = manager.set_config(config_change_request)

        return jsonify({"status": "ok",
                        "message": f"DAQ configured for bit_depth={daq_config['bit_depth']}.",
                        'config': daq_config})