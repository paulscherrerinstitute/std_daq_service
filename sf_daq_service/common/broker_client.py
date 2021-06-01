import json
import logging
import uuid
from functools import partial

from pika import BlockingConnection, ConnectionParameters, BasicProperties

from sf_daq_service.common import broker_config

_logger = logging.getLogger("BrokerClient")


class BrokerClient(object):
    def __init__(self, broker_url, status_tag, on_status_message_function):
        self.broker_url = broker_url
        self.status_tag = status_tag
        self.on_message = on_status_message_function

        self.status_queue_name = str(uuid.uuid4())
        _logger.debug(f"Status queue name: {self.status_queue_name}")

        self.connection = None
        self.channel = None

    def start(self):
        self.connection = BlockingConnection(ConnectionParameters(self.broker_url))
        self.channel = self.connection.channel()

        self.channel.exchange_declare(exchange=broker_config.STATUS_EXCHANGE,
                                      exchange_type=broker_config.STATUS_EXCHANGE_TYPE)
        self.channel.exchange_declare(exchange=broker_config.REQUEST_EXCHANGE,
                                      exchange_type=broker_config.REQUEST_EXCHANGE_TYPE)

        self.channel.queue_declare(queue=self.status_queue_name, exclusive=True, auto_delete=True)
        self.channel.queue_bind(queue=self.status_queue_name,
                                exchange=broker_config.STATUS_EXCHANGE,
                                routing_key=self.status_tag)

        self.channel.basic_qos(prefetch_count=1)
        self.channel.basic_consume(self.status_queue_name, self._on_broker_message, auto_ack=True)

        try:
            self.channel.start_consuming()
        except KeyboardInterrupt:
            self.channel.stop_consuming()

    def stop(self):
        self.connection.add_callback_threadsafe(self.channel.stop_consuming)

    def _on_broker_message(self, channel, method_frame, header_frame, body):
        try:
            request = json.loads(body.decode())
            self.on_message(header_frame.correlation_id, header_frame.headers, request)

        except Exception as e:
            _logger.exception("Error in broker listener.")

    def send_request(self, tag, message, header=None):

        header = header or {}

        _logger.info(f'Sending request to tag {tag} with header {header} and message {message}')

        body = json.dumps(message).encode()
        request_id = str(uuid.uuid4())

        send_request_f = partial(
            self.channel.basic_publish,
            broker_config.REQUEST_EXCHANGE,
            tag,
            body,
            BasicProperties(headers=header,
                            correlation_id=request_id)
        )

        self.connection.add_callback_threadsafe(send_request_f)

        return request_id
