import json
import logging
import uuid

from functools import partial
from threading import Thread
from pika import BlockingConnection, ConnectionParameters, BasicProperties

from sf_daq_service.common import broker_config

_logger = logging.getLogger("BrokerWorker")


class BrokerWorker(object):
    def __init__(self, broker_url, tag, name, on_message_function):
        self.broker_url = broker_url
        self.worker_tag = tag
        self.worker_name = name
        self.on_message_function = on_message_function

        self.request_queue_name = str(uuid.uuid4())

        self.connection = None
        self.channel = None

    def start(self):
        self.connection = BlockingConnection(ConnectionParameters(self.broker_url))
        self.channel = self.connection.channel()

        self.channel.exchange_declare(exchange=broker_config.STATUS_EXCHANGE,
                                      exchange_type=broker_config.STATUS_EXCHANGE_TYPE)
        self.channel.exchange_declare(exchange=broker_config.REQUEST_EXCHANGE,
                                      exchange_type=broker_config.REQUEST_EXCHANGE_TYPE)

        self.channel.queue_declare(queue=self.request_queue_name, auto_delete=True, exclusive=True)
        self.channel.queue_bind(queue=self.request_queue_name,
                                exchange=broker_config.REQUEST_EXCHANGE,
                                routing_key=self.worker_tag)

        self.channel.basic_qos(prefetch_count=1)
        self.channel.basic_consume(self.request_queue_name, self._on_broker_message)

        try:
            self.channel.start_consuming()
        except KeyboardInterrupt:
            self.channel.stop_consuming()

    def stop(self):
        self.connection.add_callback_threadsafe(self.channel.stop_consuming)

    def _on_broker_message(self, channel, method_frame, header_frame, body):

        try:
            request_id = header_frame.correlation_id
            self._update_status(request_id, body, broker_config.ACTION_REQUEST_START)

            request = json.loads(body.decode())

            def process_async():
                try:
                    result = self.on_message_function(request)

                except Exception as ex:
                    _logger.exception("Error while running the request in the service.")

                    reject_request_f = partial(self._reject_request, request_id,
                                               body, method_frame.delivery_tag, str(ex))
                    self.connection.add_callback_threadsafe(reject_request_f)

                else:
                    confirm_request_f = partial(self._confirm_request, request_id,
                                                body, method_frame.delivery_tag, result)
                    self.connection.add_callback_threadsafe(confirm_request_f)

            thread = Thread(target=process_async)
            thread.daemon = True
            thread.start()

        except Exception as e:
            _logger.exception("Error in broker worker.")
            self._reject_request(body, header_frame.delivery_tag, str(e))

    def _update_status(self, request_id, body, action, message=None):

        status_header = {
            "action": action,
            "source": self.worker_name,
            "message": message
        }

        self.channel.basic_publish(
            exchange=broker_config.STATUS_EXCHANGE,
            properties=BasicProperties(
                headers=status_header,
                correlation_id=request_id),
            routing_key=self.worker_name,
            body=body
        )

    def _confirm_request(self, request_id, body, delivery_tag, message=None):
        self.channel.basic_ack(delivery_tag=delivery_tag)
        self._update_status(request_id, body, broker_config.ACTION_REQUEST_SUCCESS, message)

    def _reject_request(self, request_id, body, delivery_tag, message=None):
        self.channel.basic_reject(delivery_tag=delivery_tag, requeue=False)
        self._update_status(request_id, body, broker_config.ACTION_REQUEST_FAIL, message)
