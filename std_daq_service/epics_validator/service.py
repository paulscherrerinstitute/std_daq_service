from logging import getLogger

import h5py

_logger = getLogger("EpicsValidationService")


class EpicsValidationService(object):

    def on_request(self, request_id, request):
        input_filename = request["output_file"]
        _logger.info(f"Validating request {request_id} on file {input_filename}.")

        expected_channels = request["channels"]

        with h5py.File(input_filename, mode='r') as input_file:

            missing_channels = []
            for channel in expected_channels:
                if channel not in input_file:
                    missing_channels.append(channel)

        valid = len(missing_channels) == 0

        return {
            "valid": valid,
            "missing_channels": missing_channels
        }

    def on_kill(self, request_id):
        pass
