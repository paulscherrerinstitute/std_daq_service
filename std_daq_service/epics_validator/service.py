import time
from logging import getLogger

import h5py

from std_daq_service.broker.common import ACTION_REQUEST_START, ACTION_REQUEST_SUCCESS, ACTION_REQUEST_FAIL

_logger = getLogger("EpicsValidationService")


class EpicsValidationService(object):
    def __init__(self):
        self.requests = {}
        self.headers = {}

    def validate_file(self, request_id):
        _logger.info(f"Validating request {request_id} on file {input_filename}.")
        output_file = self.requests[request_id]['output_file']
        with h5py.File(output_file, mode='r') as input_file:

            missing_channels = []
            for channel in expected_channels:
                if channel not in input_file:
                    missing_channels.append(channel)

        valid = len(missing_channels) == 0

        return {
            "valid": valid,
            "missing_channels": missing_channels
        }

    def print_run_log(self, request_id, message):
        run_log_file = self.requests[request_id].get("run_log_file")
        if run_log_file is None:
            return


    def on_request_start(self, request_id, source, output_file):
        start_pulse_id = self.requests[request_id]['start_pulse_id']
        stop_pulse_id = self.requests[request_id]['stop_pulse_id']
        n_channels = len(self.requests[request_id]['channels'])

        output_text = f'[{source}] Processing of {request_id} started in service {source}.\n'
        output_text +=  f'[{source}] Requesting file {output_file} for pulse_id range {start_pulse_id} to ' \
                        f'{stop_pulse_id} with {n_channels} channels.'

        self.print_run_log(request_id=request_id, message=output_text)


    def on_request_success(self, request_id):

    def on_request_fail(self, request_id):
        pass

    def on_status_change(self, request_id, request, header):

        if request_id not in self.requests:
            self.requests[request_id] = request
            self.headers[request_id] = []

        source = header['source']
        header_entry = (time.time(), header, source)
        self.headers[request_id].append(header_entry)

        action = header['action']
        if action == ACTION_REQUEST_START:
            output_file = request['output_file']
            self.on_request_start(request_id, source, output_file)

        elif action == ACTION_REQUEST_SUCCESS:
            self.on_request_success(request_id, source)

        elif action == ACTION_REQUEST_FAIL:
            error_message = header["message"]
            self.on_request_fail(request_id, source, error_message)
