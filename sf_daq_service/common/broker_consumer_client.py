import json
import logging

from functools import partial
from threading import Thread
from pika import BlockingConnection, ConnectionParameters, BasicProperties

from sf_daq_service.common import broker_config

_logger = logging.getLogger("BrokerListener")


class BrokerConsumerListener(object):
    def __init__(self, broker_url, service_name, on_message_function):
        self.broker_url = broker_url
        self.service_name = service_name
        self.on_message_function = on_message_function

        self.connection = None
        self.channel = None

    def start_consuming(self):
        self.connection = BlockingConnection(ConnectionParameters(self.broker_url))
        self.channel = self.connection.channel()

        self.channel.exchange_declare(exchange=broker_config.STATUS_EXCHANGE,
                                      exchange_type=broker_config.STATUS_EXCHANGE_TYPE)
        self.channel.exchange_declare(exchange=broker_config.REQUEST_EXCHANGE,
                                      exchange_type=broker_config.REQUEST_EXCHANGE_TYPE)

        self.channel.queue_declare(queue=self.service_name, auto_delete=True)
        self.channel.queue_bind(queue=self.service_name,
                                exchange=broker_config.REQUEST_EXCHANGE,
                                routing_key=self.service_name)

        self.channel.basic_qos(prefetch_count=1)
        self.channel.basic_consume(self.service_name, self._on_broker_message)

        try:
            self.channel.start_consuming()
        except KeyboardInterrupt:
            self.channel.stop_consuming()

    def stop(self):
        self.connection.add_callback_threadsafe(self.channel.stop_consuming)

    def _on_broker_message(self, channel, method_frame, header_frame, body):

        try:
            self._update_status(body, broker_config.ACTION_REQUEST_START)

            request = json.loads(body.decode())

            def process_async():
                try:
                    result = self.on_message_function(request)

                except Exception as ex:
                    _logger.exception("Error while running the request in the service.")

                    reject_request_f = partial(self._reject_request, body, method_frame.delivery_tag, str(ex))
                    self.connection.add_callback_threadsafe(reject_request_f)

                else:
                    confirm_request_f = partial(self._confirm_request, body, method_frame.delivery_tag, result)
                    self.connection.add_callback_threadsafe(confirm_request_f)

            thread = Thread(target=process_async)
            thread.daemon = True
            thread.start()

        except Exception as e:
            _logger.exception("Error in broker listener.")
            self._reject_request(body, header_frame.delivery_tag, str(e))

    def _update_status(self, body, action, message=None):

        status_header = {
            "action": action,
            "source": self.service_name,
            "message": message
        }

        self.channel.basic_publish(
            exchange=broker_config.STATUS_EXCHANGE,
            properties=BasicProperties(
                headers=status_header),
            routing_key=self.service_name,
            body=body
        )

    def _confirm_request(self, body, delivery_tag, message=None):
        self.channel.basic_ack(delivery_tag=delivery_tag)
        self._update_status(body, broker_config.ACTION_REQUEST_SUCCESS, message)

    def _reject_request(self, body, delivery_tag, message=None):
        self.channel.basic_reject(delivery_tag=delivery_tag, requeue=False)
        self._update_status(body, broker_config.ACTION_REQUEST_FAIL, message)
