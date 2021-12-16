from logging import getLogger

_logger = getLogger("EpicsValidationService")


class EpicsValidationService(object):

    def on_request(self, request_id, request):
        pass

    def on_kill(self, request_id):
        pass
