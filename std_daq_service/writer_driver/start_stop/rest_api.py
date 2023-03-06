import logging
from flask import request, make_response, Flask
from std_daq_service.writer_driver.start_stop.driver import WriterDriver

_logger = logging.getLogger(__name__)


class StartStopManager(object):
    def __init__(self, driver: WriterDriver):
        self.driver = driver

    def get_status(self):
        return self.driver.get_status()

    def start_writing(self, request_data):
        errors = []
        if 'filename' not in request_data:
            errors.append("Attribute 'filename' missing in request JSON.")
        if 'n_images' not in request_data:
            errors.append("Attribute 'n_images' missing in request JSON.")
        if errors:
            raise Exception('\n'.join(errors))

        status = self.get_status()
        if status['state'] == "READY":
            self.driver.send_command(WriterDriver.WRITE_COMMAND, request_data)
        else:
            raise Exception(f"Writer not ready to start. Writer state: {status['state']}.")

        return self.get_status()

    def stop_writing(self):
        status = self.get_status()

        if status['state'] == "WRITING":
            self.driver.send_command(WriterDriver.STOP_COMMAND)

        return self.get_status()


def register_rest_interface(app: Flask, manager: StartStopManager):

    @app.get("/write")
    def get_status():
        status = manager.get_status()
        return {'state': 'ok', 'message': 'Collected status.', 'writer_status': status}

    @app.post("/write")
    def start_writing():
        status = manager.start_writing(request.json())
        return {'state': 'ok', 'message': 'Writing started.', 'writer_status': status}

    @app.delete("/write")
    def stop_writing():
        status = manager.stop_writing()
        return {'state': 'ok', 'message': 'Writing stopped.', 'writer_status': status}

    @app.errorhandler(Exception)
    def error_handler(error):
        error_text = str(error.exception)
        _logger.error(error_text)
        return make_response({"state": "error", "message": error_text}, 200)
