import json
import uuid
from functools import partial
from logging import getLogger
from threading import Thread

from pika import BlockingConnection, ConnectionParameters, BasicProperties

from std_daq_service.common.broker_utils import bind_queue_to_exchange

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


class BrokerService(object):
    def __init__(self, broker_url, tag, service_name):
        self.tag = tag
        self.service_name = service_name

        self.connection = BlockingConnection(ConnectionParameters(broker_url))
        self.channel = self.connection.channel()
        self.channel.basic_qos(prefetch_count=1)

        self.channel.exchange_declare(exchange=REQUEST_EXCHANGE, exchange_type=REQUEST_EXCHANGE_TYPE)
        self.channel.exchange_declare(exchange=STATUS_EXCHANGE, exchange_type=STATUS_EXCHANGE_TYPE)
        self.channel.exchange_declare(exchange=KILL_EXCHANGE, exchange_type=KILL_EXCHANGE_TYPE)

        bind_queue_to_exchange(self.channel, REQUEST_EXCHANGE, tag, self._request_callback, False)
        bind_queue_to_exchange(self.channel, KILL_EXCHANGE, tag, self._kill_callback, True)

        self.user_request_callback = None
        self.user_kill_callback = None
        self.user_status_callback = None

        self.request_id_cache = {}

        _logger.info(f"Starting with tag {tag} and service_name {service_name} on broker_url {broker_url}.")

        def start_consuming():
            try:
                self.channel.start_consuming()
            except KeyboardInterrupt:
                self.channel.stop_consuming()

        self.thread = Thread(target=start_consuming)
        self.thread.start()

    def __del__(self):
        self.stop()

    def _request_callback(self, channel, method_frame, header_frame, body):

        if self.user_request_callback is None:
            return

        def request_f():
            request_id = header_frame.correlation_id
            delivery_tag = header_frame.delivery_tag
            _logger.info(f"Received request_id {request_id} with delivery_tag {delivery_tag}.")

            request = json.loads(body.decode())
            _logger.debug(f"Received request {request}")

            try:
                self.channel.basic_publish(STATUS_EXCHANGE, self.tag, body, BasicProperties(
                    correlation_id=request_id, headers={
                        'action': ACTION_REQUEST_START,
                        'source': self.client_name,
                        'message': None
                    }))

                result = self.user_request_callback(request_id, request)

                self.channel.basic_publish(STATUS_EXCHANGE, self.tag, body, BasicProperties(
                    correlation_id=request_id, headers={
                        'action': ACTION_REQUEST_SUCCESS,
                        'source': self.client_name,
                        'message': result
                    }))
                self.channel.basic_ack(delivery_tag=delivery_tag)

            except Exception as e:
                _logger.exception("Error while executing user_request_callback.")
                self._update_status(request_id, {
                    'action': ACTION_REQUEST_FAIL,
                    'source': self.client_name,
                    'message': str(e)
                })
                self.channel.basic_reject(delivery_tag=delivery_tag, requeue=False)

        thread = Thread(target=request_f)
        thread.daemon = True
        thread.start()

    def _kill_callback(self, channel, method_frame, header_frame, body):

        if self.user_kill_callback is None:
            pass

        request_id = header_frame.correlation_id
        _logger.info(f"Received kill for request_id {request_id}.")

        self.user_kill_callback(request_id)

    def block(self):
        self.thread.join()

    def stop(self):
        _logger.info("Stopping connection.")

        self.connection.add_callback_threadsafe(self.channel.stop_consuming)
        self.thread.join()
