import argparse
import json
import logging
import sys

from flask import Flask, jsonify, make_response, request

from std_daq_service.broker.common import TEST_BROKER_URL
from std_daq_service.rest.manager import RestManager
from std_daq_service.rest.request_factory import (
    build_user_response,
    extract_write_request,
)
from std_daq_service.start_utils import default_service_setup

_logger = logging.getLogger("RestProxyService")


class NoTraceBackWithLineNumber(Exception):
    def __init__(self, msg):
        if type(msg).__name__ in ["ConnectionError", "ReadTimeout"]:
            print(
                "\n ConnectionError/ReadTimeout: it seems that the server "
                "is not running...\n"
            )
        try:
            ln = sys.exc_info()[-1].tb_lineno
        except AttributeError:
            ln = inspect.currentframe().f_back.f_lineno
        self.args = (
            "{0.__name__} (line {1}): {2}".format(type(self), ln, msg),
        )
        sys.tracebacklimit = None
        return None


class StdDaqAPIError(NoTraceBackWithLineNumber):
    pass


def start_rest_api(service_name, broker_url, tag, config_file):
    app = Flask(service_name)
    manager = RestManager(broker_url=broker_url, tag=tag)

    @app.route("/alive", methods=["GET"])
    def alive():
        return jsonify({"status": 200, "alive": "True"})

    @app.route("/write_sync", methods=["POST"])
    def write_sync_request():
        response_dict = {}

        try:
            message = extract_write_request(request.json)
        except Exception as e:
            error_msg = str(StdDaqAPIError(e))

        if not error_msg:
            request_id, broker_response = manager.write_sync(message)
            response_dict = {
                "request_id": request_id,
                "response": build_user_response(response=broker_response),
            }
        elif error_msg:
            response_dict["error"] = error_msg
        else:
            response_dict["error"] = "Something went wrong..."
        return jsonify(response_dict)

    @app.route("/write_async", methods=["POST"])
    def write_async_request():
        response_dict = {}
        try:
            message = extract_write_request(request.json)
        except Exception as e:
            error_msg = str(StdDaqAPIError(e))

        if not error_msg:
            request_id = manager.write_async(message)
            response_dict = {"request_id": request_id}
        elif error_msg:
            response_dict["error"] = error_msg
        else:
            response_dict["error"] = "Something went wrong..."
        return jsonify(response_dict)

    @app.route("/write_kill", methods=["POST"])
    def write_kill():
        kill_request = request.json
        response_dict = {}
        error_msg = ""
        if "request_id" not in kill_request:
            response_dict["error"] = 'Mandatory field "request_id" missing.'
        else:
            request_id = kill_request["request_id"]
            try:
                broker_response = manager.kill_sync(request_id)
            except Exception as e:
                response_dict["error"] = str(StdDaqAPIError(e))
            if "error" not in response_dict:
                response_dict = {
                    "request_id": request_id,
                    "response": build_user_response(response=broker_response),
                }
        return jsonify(response_dict)

    app.run(host="0.0.0.0", port=5000)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="SLS Rest Service for the Gigafrost Camera"
    )
    parser.add_argument(
        "tag",
        type=str,
        help="Tag on which the proxy listens to statuses and sends requests.",
    )
    parser.add_argument(
        "--broker_url",
        default=TEST_BROKER_URL,
        help="Address of the broker to connect to.",
    )

    service_name, config, args = default_service_setup(parser)
    broker_url = args.broker_url
    tag = args.tag

    _logger.info(f"Service {service_name} connecting to {broker_url}.")

    start_rest_api(
        service_name=service_name,
        broker_url=args.broker_url,
        tag=args.tag,
        config_file=args.json_config_file,
    )

    _logger.info(f"Service {args.service_name} stopping.")
