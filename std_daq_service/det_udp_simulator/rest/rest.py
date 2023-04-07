from flask import request, jsonify

START_ENDPOINT = "/start"
STOP_ENDPOINT = "/stop"
STATUS_ENDPOINT = "/status"


def register_rest_interface(app, manager):
    @app.route(START_ENDPOINT, methods=['POST'])
    def start_request():
        json_request = request.json
        n_images = json_request['n_images']

        generator_status = manager.start(n_images)

        return jsonify({"status": "ok",
                        "message": "UDP sending started.",
                        'generator': generator_status})

    @app.route(STOP_ENDPOINT, methods=['POST'])
    def stop_request():
        generator_status = manager.stop()

        return jsonify({"status": "ok",
                        "message": "UDP sending stopped.",
                        'generator': generator_status})

    @app.route(STATUS_ENDPOINT, methods=['GET'])
    def get_status_request():
        generator_status = manager.get_status()

        return jsonify({"status": "ok",
                        "message": f"Generator is {generator_status['state']}",
                        'generator': generator_status})

