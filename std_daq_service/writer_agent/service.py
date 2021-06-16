from threading import Event

from std_daq_service.common.protocol import ImageMetadata
from std_daq_service.writer_agent.start import _logger


class RequestWriterService(object):
    def __init__(self):
        self.request_id = None
        self.request = None

        self.request_completed = Event()
        self.request_result = None
        self.interrupt_request = None

        self.i_image = None

    def on_stream_message(self, recv_bytes: bytes):
        if self.request is None:
            return None

        if self.interrupt_request is not None:
            if self.request_id == self.interrupt_request:
                self._complete_request()
            else:
                self.interrupt_request = None

        image_meta = ImageMetadata.from_buffer_copy(recv_bytes)

        if self.i_image is None:
            self.i_image = 0
            self.request_result = {
                'start_pulse_id': image_meta.pulse_id,
                'n_images': self.request['n_images'],
                'output_file': self.request["output_file"]
            }

        writer_stream_message = {
            "output_file": self.request["output_file"],
            "i_image": self.i_image,
            "n_images": self.request["n_images"],
            "image_metadata": image_meta.as_dict()
        }

        if self.i_image + 1 == self.request["n_images"]:
            self.request_result["end_pulse_id"] = image_meta.pulse_id
            self._complete_request()
        else:
            self.i_image += 1

        return writer_stream_message

    def _complete_request(self):
        self.request = None
        self.i_image = None
        self.request_completed.set()
        self.interrupt_request = None

    def on_broker_message(self, request_id, request):
        self._set_request_and_wait(request_id, request)
        self.request_completed.clear()

        return self.request_result

    def _set_request_and_wait(self, request_id, request):
        _logger.info(f"Starting to work on request_id {request_id}, {request}")
        self.request_result = None
        self.request = request
        self.request_completed.wait()

    def on_kill_request(self, request_id):
        self.interrupt_request = request_id