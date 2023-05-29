import time
from logging import getLogger

from std_daq_service.broker.common import ACTION_REQUEST_START, ACTION_REQUEST_SUCCESS, ACTION_REQUEST_FAIL

_logger = getLogger("EpicsValidationService")


class EpicsValidationService(object):
    def __init__(self, file_validator, primary_service_name):
        self.requests = {}
        self.headers = {}
        self.file_validator = file_validator
        self.primary_service_name = primary_service_name

    def print_run_log(self, request_id, message):
        run_log_file = self.requests[request_id].get("run_log_file")

        if run_log_file is None:
            return

        _logger.debug(message)

        with open(run_log_file, 'a') as output_file:
            output_file.write(message)

    def on_request_start(self, request_id, source, output_file):
        start_pulse_id = self.requests[request_id]['start_pulse_id']
        stop_pulse_id = self.requests[request_id]['stop_pulse_id']
        n_channels = len(self.requests[request_id]['channels'])

        output_text = f'[{source}] Processing of {request_id} started in service {source}.\n'
        output_text += f'[{source}] Requesting file {output_file} for pulse_id range {start_pulse_id} to ' \
                       f'{stop_pulse_id} with {n_channels} channels.\n'

        self.print_run_log(request_id=request_id, message=output_text)

    def on_request_success(self, request_id, source, output_file):
        start_time = self.headers[request_id][source][0][0]
        time_delta = time.time() - start_time

        output_text = f'[{source}] Request {request_id} completed in {time_delta:.2f} seconds.\n'
        output_text += f'[{source}] Output file analysis:\n'

        try:
            validation_result = self.file_validator(request_id, self.requests[request_id])
        except Exception as e:
            validation_result = [f"Count not process output file: {e}"]

        for line in validation_result:
            output_text += f'\t{line}\n'

        self.print_run_log(request_id=request_id, message=output_text)

    def on_request_fail(self, request_id, source, error_message):
        output_text = f'[{source}] Request {request_id} failed. Error:\n{error_message}\n'

        self.print_run_log(request_id=request_id, message=output_text)

    def on_status_change(self, request_id, request, header):

        source = header['source']
        if source != self.primary_service_name:
            return

        if request_id is None:
            _logger.warning("Received request_id == None. One of the clients is not playing nice.")
            return

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
