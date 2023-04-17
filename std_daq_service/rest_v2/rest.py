from flask import request, jsonify, Response

from std_daq_service.rest_v2.daq import DaqRestManager
from std_daq_service.rest_v2.utils import get_parameters_from_write_request
from std_daq_service.rest_v2.writer import WriterRestManager
from std_daq_service.rest_v2.simulation import SimulationRestManager

# TODO: Separate the drivers based on the REST namespace.
WRITER_WRITE_SYNC_ENDPOINT = "/writer/write_sync"
WRITER_WRITE_ASYNC_ENDPOINT = "/writer/write_async"
WRITER_STATUS_ENDPOINT = "/writer/status"
WRITER_STOP_ENDPOINT = "/writer/stop"

SIM_STATUS_ENDPOINT = '/simulation/status'
SIM_START_ENDPOINT = '/simulation/start'
SIM_STOP_ENDPOINT = '/simulation/stop'

DAQ_LIVE_STREAM_ENDPOINT = '/daq/live'
DAQ_CONFIG_ENDPOINT = '/daq/config'
DAQ_STATS_ENDPOINT = '/daq/stats'
DAQ_LOGS_ENDPOINT = '/daq/logs/<int:n_logs>'
DAQ_DEPLOYMENT_STATUS_ENDPOINT = '/daq/deployment'


def register_rest_interface(app, writer_manager: WriterRestManager, sim_manager: SimulationRestManager,
                            daq_manager: DaqRestManager):
    detector_name = daq_manager.get_config()['detector_name']

    @app.route(WRITER_WRITE_SYNC_ENDPOINT, methods=['POST'])
    def write_sync_request():
        json_request = request.json
        output_file, n_images = get_parameters_from_write_request(json_request)

        writer_status = writer_manager.write_sync(output_file, n_images)

        return jsonify({"status": "ok",
                        "message": "Writing finished.",
                        'writer': writer_status})

    @app.route(WRITER_WRITE_ASYNC_ENDPOINT, methods=['POST'])
    def write_async_request():
        json_request = request.json
        output_file, n_images = get_parameters_from_write_request(json_request)

        writer_status = writer_manager.write_async(output_file, n_images)

        return jsonify({"status": "ok",
                        "message": "Writing started.",
                        'writer': writer_status})

    @app.route(WRITER_STATUS_ENDPOINT)
    def get_writer_status_request():
        writer_status = writer_manager.get_status()

        return jsonify({"status": "ok",
                        "message": f"Writer is {writer_status['state']}",
                        'writer': writer_status})

    @app.route(WRITER_STOP_ENDPOINT, methods=['POST'])
    def stop_writing_request():
        writer_status = writer_manager.stop_writing()

        return jsonify({"status": "ok",
                        "message": "Writing stopped.",
                        'writer': writer_status})

    @app.route(SIM_STATUS_ENDPOINT)
    def get_sim_status_request():
        status = sim_manager.get_status()

        return jsonify({"status": "ok",
                        "message": f"Simulator for {detector_name}.",
                        'simulator': status})

    @app.route(SIM_START_ENDPOINT)
    def start_sim_request():
        sim_manager.start()
        return get_sim_status_request()

    @app.route(SIM_STOP_ENDPOINT)
    def stop_sim_request():
        sim_manager.stop()
        return get_sim_status_request()

    @app.route(DAQ_LIVE_STREAM_ENDPOINT)
    def get_daq_live_stream_request():
        return Response(live_stream_generator, mimetype='multipart/x-mixed-replace; boundary=frame')

    @app.route(DAQ_CONFIG_ENDPOINT, methods=['GET'])
    def get_daq_config_request():
        daq_config = daq_manager.get_config()
        return jsonify({"status": "ok",
                        "message": f"DAQ configured for bit_depth={daq_config['bit_depth']}.",
                        'config': daq_config})

    @app.route(DAQ_CONFIG_ENDPOINT, methods=['POST'])
    def set_daq_config_request():
        config_change_request = request.json
        daq_config = daq_manager.set_config(config_change_request)

        return jsonify({"status": "ok",
                        "message": f"DAQ configured for bit_depth={daq_config['bit_depth']}.",
                        'config': daq_config})

    @app.route(DAQ_STATS_ENDPOINT)
    def get_daq_stats_request():
        stats = daq_manager.get_stats()
        return jsonify({"status": "ok",
                        "message": f"DAQ statistics for {detector_name}.",
                        'stats': stats})

    @app.route(DAQ_LOGS_ENDPOINT)
    def get_daq_logs_request(n_logs):
        logs = daq_manager.get_logs(n_logs)
        return jsonify({"status": "ok",
                        "message": f"DAQ logs for {detector_name}.",
                        'logs': logs})

    @app.route(DAQ_DEPLOYMENT_STATUS_ENDPOINT)
    def get_deployment_status_request():
        return jsonify({"status": "ok",
                        "message": f"DAQ logs for {detector_name}.",
                        'deployment': daq_manager.get_deployment_status()})
