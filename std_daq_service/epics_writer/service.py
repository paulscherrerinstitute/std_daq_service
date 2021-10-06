from logging import getLogger
from threading import Event

import zmq

from std_daq_service.protocol import ImageMetadata

_logger = getLogger("EpicsWriterService")


class EpicsWriterService(object):
    def __init__(self, buffer_folder):
        _logger.info(f"Starting on epics buffer folder {buffer_folder}.")

        self.buffer_folder = buffer_folder

    def on_request(self, request_id, request):
        self.interrupt_request.clear()
        self.current_request_id = request_id

        n_images = request['n_images']

        _logger.info(f"Starting write request for n_images {writer_stream_data['n_images']} "
                     f"in {writer_stream_data['output_file']}")

    def on_kill(self, request_id):
        if self.current_request_id == request_id:
            self.interrupt_request.set()
