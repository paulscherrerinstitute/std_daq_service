import time
from logging import getLogger

import h5py

from std_daq_service.broker.common import ACTION_REQUEST_START, ACTION_REQUEST_SUCCESS, ACTION_REQUEST_FAIL

_logger = getLogger("EpicsValidationService")


class EpicsValidationService(object):
    def __init__(self):
        self.requests = {}
        self.headers = {}

    def validate_file(self, request_id, output_file):
        _logger.info(f"Validating request {request_id} file {output_file}.")
        expected_channels = self.requests[request_id]['channels']

        with h5py.File(output_file, mode='r') as input_file:

            missing_channels = []
            for channel in expected_channels:
                if channel not in input_file:
                    missing_channels.append(f"Missing pv {channel}")

        return missing_channels

    def print_run_log(self, request_id, message):
        run_log_file = self.requests[request_id].get("run_log_file")

        if run_log_file is None:
            return

        print(message)

    def on_request_start(self, request_id, source, output_file):
        start_pulse_id = self.requests[request_id]['start_pulse_id']
        stop_pulse_id = self.requests[request_id]['stop_pulse_id']
        n_channels = len(self.requests[request_id]['channels'])

        output_text = f'[{source}] Processing of {request_id} started in service {source}.\n'
        output_text += f'[{source}] Requesting file {output_file} for pulse_id range {start_pulse_id} to ' \
                       f'{stop_pulse_id} with {n_channels} channels.'

        self.print_run_log(request_id=request_id, message=output_text)

    def on_request_success(self, request_id, source, output_file):
        start_time = self.headers[request_id][source][0][0]
        time_delta = time.time() - start_time

        output_text = f'[{source}] Request {request_id} completed in {time_delta:.2f} seconds.\n'
        output_text += f'[{source}] Output file analysis:\n'

        try:
            validation_result = self.validate_file(request_id, output_file)
        except Exception as e:
            validation_result = f"Count not process output file: {e}"

        for line in validation_result:
            output_text += f'\t{line}\n'

        self.print_run_log(request_id=request_id, message=output_text)

    def on_request_fail(self, request_id, source, error_message):
        output_text = f'[{source}] Request {request_id} failed. Error:\n{error_message}'

        self.print_run_log(request_id=request_id, message=output_text)

    def on_status_change(self, request_id, request, header):

        source = header['source']
        if request_id not in self.requests:
            _logger.debug(f"Received new request {request_id}.")
            self.requests[request_id] = request
            self.headers[request_id] = {source: []}

        header_entry = (time.time(), header, source)
        self.headers[request_id][source].append(header_entry)

        output_file = request['output_file']
        action = header['action']

        _logger.debug(f"Received action {action} for request {request_id} from {source}.")

        if action == ACTION_REQUEST_START:
            self.on_request_start(request_id, source, output_file)
            _logger.info(f"Request {request_id} started in {source}.")

        elif action == ACTION_REQUEST_SUCCESS:
            _logger.info(f"Request {request_id} completed successfully.")

            self.on_request_success(request_id, source, output_file)

            self.cleanup_request(request_id)

        elif action == ACTION_REQUEST_FAIL:
            error_message = header["message"]
            _logger.info(f'Request {request_id} failed: {error_message}')

            self.on_request_fail(request_id, source, error_message)

            self.cleanup_request(request_id)

    def cleanup_request(self, request_id):
        del self.requests[request_id]
        del self.headers[request_id]

        _logger.debug(f"Request {request_id} removed from cache.")
