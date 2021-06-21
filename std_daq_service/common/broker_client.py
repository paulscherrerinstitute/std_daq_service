import json
import uuid
from functools import partial
from logging import getLogger
from threading import Thread

from pika import BlockingConnection, ConnectionParameters, BasicProperties

TEST_BROKER_URL = '127.0.0.1'

STATUS_EXCHANGE = 'status'
STATUS_EXCHANGE_TYPE = 'fanout'

REQUEST_EXCHANGE = 'request'
REQUEST_EXCHANGE_TYPE = 'topic'

KILL_EXCHANGE = 'kill'
KILL_EXCHANGE_TYPE = 'topic'

ACTION_REQUEST_START = "request_start"
ACTION_REQUEST_SUCCESS = "request_success"
ACTION_REQUEST_FAIL = "request_fail"

_logger = getLogger("RabbitMQConnection")


class BrokerClient(object):
    def __init__(self, broker_url, tag, status_callback=None, request_callback=None, kill_callback=None):

        self.connection = BlockingConnection(ConnectionParameters(broker_url))
        self.channel = self.connection.channel()
        self.channel.basic_qos(prefetch_count=1)
        self.tag = tag

        self.channel.exchange_declare(exchange=REQUEST_EXCHANGE, exchange_type=REQUEST_EXCHANGE_TYPE)
        self.channel.exchange_declare(exchange=STATUS_EXCHANGE, exchange_type=STATUS_EXCHANGE_TYPE)
        self.channel.exchange_declare(exchange=KILL_EXCHANGE, exchange_type=KILL_EXCHANGE_TYPE)

        if status_callback is not None:
            self._bind_queue(STATUS_EXCHANGE, tag, status_callback, True)

        if request_callback is not None:
            self._bind_queue(REQUEST_EXCHANGE, tag, request_callback, False)

        if kill_callback is not None:
            self._bind_queue(KILL_EXCHANGE, tag, kill_callback, True)

        def start_consuming():
            try:
                self.channel.start_consuming()
            except KeyboardInterrupt:
                self.channel.stop_consuming()

        self.thread = Thread(target=start_consuming)
        self.thread.start()

    def __del__(self):
        self.stop()

    def _bind_queue(self, exchange, tag, callback, auto_ack):
        queue = str(uuid.uuid4())

        _logger.info(f"Binding queue {queue} to exchange {exchange} with tag {tag}.")

        self.channel.queue_declare(queue, auto_delete=True, exclusive=True)
        self.channel.queue_bind(queue=queue,
                                exchange=exchange,
                                routing_key=tag)

        self.channel.basic_consume(queue, callback, auto_ack=auto_ack)

    def block(self):
        self.thread.join()

    def stop(self):
        _logger.info("Stopping connection.")

        self.connection.add_callback_threadsafe(self.channel.stop_consuming)
        self.thread.join()

    def send_request(self, message, header=None):
        header = header or {}

        _logger.info(f'Sending request to tag {self.tag} with header {header} and message {message}')

        body = json.dumps(message).encode()
        request_id = str(uuid.uuid4())

        send_request_f = partial(
            self.channel.basic_publish, REQUEST_EXCHANGE, self.tag, body,
            BasicProperties(headers=header,
                            correlation_id=request_id)
        )

        self.connection.add_callback_threadsafe(send_request_f)

        return request_id

    def kill_request(self, request_id):
        _logger.info(f'Sending kill request to tag {self.tag} with request_id {request_id}.')

        kill_request_f = partial(
            self.channel.basic_publish, KILL_EXCHANGE, self.tag, "",
            BasicProperties(headers={},
                            correlation_id=request_id)
        )

        self.connection.add_callback_threadsafe(kill_request_f)

    def update_status(self, request_id, message, header):

        _logger.info(f"Updating worker status: {header}")
        properties = BasicProperties(headers=header, correlation_id=request_id)

        update_status_f = partial(
            self.request_channel.basic_publish,
            STATUS_EXCHANGE, self.tag, message, properties)

        self.connection.add_callback_threadsafe(update_status_f)
