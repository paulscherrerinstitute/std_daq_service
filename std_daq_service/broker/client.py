import json
import uuid
from functools import partial
from logging import getLogger

from pika import BasicProperties

from std_daq_service.broker.common import BrokerClientBase, REQUEST_EXCHANGE, STATUS_EXCHANGE, KILL_EXCHANGE

_logger = getLogger("BrokerClient")


class BrokerClient(BrokerClientBase):
    def __init__(self, broker_url, tag, status_callback=None):
        super().__init__(broker_url, tag)

        self.bind_queue(STATUS_EXCHANGE, tag, self._status_callback, True)

        self.user_status_callback = status_callback

        _logger.info(f"Broker client starting.")

        self.start()

    def _status_callback(self, channel, method_frame, header_frame, body):
        if self.user_status_callback is None:
            return

        request_id = header_frame.correlation_id
        _logger.debug(f"Received status for request_id {request_id}.")

        request = json.loads(body.decode())
        header = header_frame.headers

        self.user_status_callback(request_id, request, header)

    def send_request(self, request, header=None):
        header = header or {}

        _logger.debug(f'Sending request to tag {self.tag} with header {header} and message {request}')

        body = json.dumps(request).encode()
        request_id = str(uuid.uuid4())
        properties = BasicProperties(headers=header, correlation_id=request_id)

        send_request_f = partial(
            self.channel.basic_publish,
            REQUEST_EXCHANGE, self.tag, body, properties
        )

        self.connection.add_callback_threadsafe(send_request_f)

        return request_id

    def kill_request(self, request_id):
        _logger.info(f'Sending kill request to tag {self.tag} with request_id {request_id}.')

        properties = BasicProperties(headers={}, correlation_id=request_id)

        kill_request_f = partial(
            self.channel.basic_publish,
            KILL_EXCHANGE, self.tag, "", properties)

        self.connection.add_callback_threadsafe(kill_request_f)
