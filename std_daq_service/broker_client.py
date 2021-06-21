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
    def __init__(self, broker_url, tag):

        self.connection = BlockingConnection(ConnectionParameters(broker_url))
        self.channel = self.connection.channel()
        self.channel.basic_qos(prefetch_count=1)
        self.tag = tag

        self.channel.exchange_declare(exchange=REQUEST_EXCHANGE, exchange_type=REQUEST_EXCHANGE_TYPE)
        self.channel.exchange_declare(exchange=STATUS_EXCHANGE, exchange_type=STATUS_EXCHANGE_TYPE)
        self.channel.exchange_declare(exchange=KILL_EXCHANGE, exchange_type=KILL_EXCHANGE_TYPE)

        self._bind_queue(STATUS_EXCHANGE, tag, self._status_callback, True)
        self._bind_queue(REQUEST_EXCHANGE, tag, self._request_callback, False)
        self._bind_queue(KILL_EXCHANGE, tag, self._kill_callback, True)

        self.user_request_callback = None
        self.user_kill_callback = None
        self.user_status_callback = None

        self.request_id_cache = {}

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

    def _status_callback(self):
        if self.user_status_callback is None:
            return

    def _request_callback(self, channel, method_frame, header_frame, body):

        if self.user_request_callback is None:
            return

        try:
            request_id = header_frame.correlation_id
            delivery_tag = header_frame.delivery_tag
            self.request_id_cache[request_id] = delivery_tag
            _logger.info(f"Received request_id {request_id} with delivery_tag {delivery_tag}.")

            request = json.loads(body.decode())
            _logger.debug(f"Received request {request}")

            self.user_request_callback(request_id, request)

        except Exception as e:
            _logger.exception("Error while asking worker to process request.")

            self._reject_request(body, header_frame.delivery_tag, str(e))

    def complete_request(self, request_id):
        if request_id not in self.request_id_cache:
            raise ValueError("Request_id not present in cache.")

        delivery_tag = self.request_id_cache[request_id]
        del self.request_id_cache[request_id]

        def ack_request_f():
            pass

        self.connection.add_callback_threadsafe(ack_request_f)

    def reject_request(self, request_id):
        if request_id not in self.request_id_cache:
            raise ValueError("Request_id not present in cache.")

        delivery_tag = self.request_id_cache[request_id]
        del self.request_id_cache[request_id]

        def nack_request_f():
            pass

        self.connection.add_callback_threadsafe(nack_request_f)

    def _kill_callback(self):
        if self.user_kill_callback is None:
            pass

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

    def update_status(self, request_id, message, header):

        _logger.info(f'Updating status to tag {self.tag} with request_id {request_id} '
                     f'with header {header} and message {message}')

        body = json.dumps(message).encode()
        properties = BasicProperties(headers=header, correlation_id=request_id)

        update_status_f = partial(
            self.channel.basic_publish,
            STATUS_EXCHANGE, self.tag, body, properties)

        self.connection.add_callback_threadsafe(update_status_f)
