import json
import logging
import uuid

from functools import partial
from threading import Thread
from pika import BlockingConnection, ConnectionParameters, BasicProperties

from std_daq_service.common import broker_config

_logger = logging.getLogger("BrokerWorker")


class BrokerWorker(object):
    # TODO: Add on_kill_message_function
    def __init__(self, broker_url, request_tag, name, on_request_message_function):
        self.broker_url = broker_url
        self.request_tag = request_tag
        self.worker_name = name
        self.on_message_function = on_request_message_function
        _logger.info(f"Starting worker on tag {self.request_tag} with name {self.worker_name}.")

        self.request_queue_name = str(uuid.uuid4())
        self.kill_queue_name = str(uuid.uuid4())
        _logger.debug(f'Request queue {self.request_queue_name}, kill queue {self.kill_queue_name}.')

        self.connection = None
        self.request_channel = None
        self.kill_channel = None

    def start(self):
        self.connection = BlockingConnection(ConnectionParameters(self.broker_url))

        # Request and status exchanges.
        self.request_channel = self.connection.channel()

        self.request_channel.exchange_declare(exchange=broker_config.STATUS_EXCHANGE,
                                              exchange_type=broker_config.STATUS_EXCHANGE_TYPE)
        self.request_channel.exchange_declare(exchange=broker_config.REQUEST_EXCHANGE,
                                              exchange_type=broker_config.REQUEST_EXCHANGE_TYPE)

        self.request_channel.queue_declare(queue=self.request_queue_name, auto_delete=True, exclusive=True)
        self.request_channel.queue_bind(queue=self.request_queue_name,
                                        exchange=broker_config.REQUEST_EXCHANGE,
                                        routing_key=self.request_tag)

        self.request_channel.basic_qos(prefetch_count=1)
        self.request_channel.basic_consume(self.request_queue_name, self._on_broker_message)

        # Kill exchange.
        self.kill_channel = self.connection.channel()

        self.kill_channel.exchange_declare(exchange=broker_config.KILL_EXCHANGE,
                                           exchange_type=broker_config.KILL_EXCHANGE_TYPE)

        self.kill_channel.queue_declare(self.kill_queue_name, auto_delete=True, exclusive=True)
        self.kill_channel.queue_bind(queue=self.kill_queue_name,
                                     exchange=broker_config.KILL_EXCHANGE,
                                     routing_key=self.request_tag)

        self.kill_channel.basic_consume(self.kill_queue_name, self._on_kill_message, auto_ack=True)

        try:
            _logger.info("Start consuming.")
            self.request_channel.start_consuming()
        except KeyboardInterrupt:
            self.request_channel.stop_consuming()

    def stop(self):
        self.connection.add_callback_threadsafe(self.request_channel.stop_consuming)

    def _on_broker_message(self, channel, method_frame, header_frame, body):

        try:
            request_id = header_frame.correlation_id
            _logger.info(f"Received request_id {request_id}.")

            self._update_status(request_id, body, broker_config.ACTION_REQUEST_START)

            request = json.loads(body.decode())
            _logger.debug(f"Received request {request}")

            def process_async():
                try:
                    result = self.on_message_function(request_id, request)

                except Exception as ex:
                    _logger.exception("Error while running the request in the service.")

                    reject_request_f = partial(self._reject_request, request_id,
                                               body, method_frame.delivery_tag, str(ex))
                    self.connection.add_callback_threadsafe(reject_request_f)

                else:
                    _logger.info("Request completed successfully.")

                    confirm_request_f = partial(self._confirm_request, request_id,
                                                body, method_frame.delivery_tag, result)
                    self.connection.add_callback_threadsafe(confirm_request_f)

            thread = Thread(target=process_async)
            thread.daemon = True
            thread.start()

        except Exception as e:
            _logger.exception("Error in broker worker.")
            self._reject_request(body, header_frame.delivery_tag, str(e))

    def _on_kill_message(self, channel, method_frame, header_frame, body):
        # TODO: Figure out a signalization way.
        pass

    def _update_status(self, request_id, body, action, message=None):

        status_header = {
            "action": action,
            "source": self.worker_name,
            "message": message
        }

        _logger.info(f"Updating worker status: {status_header}")

        self.request_channel.basic_publish(
            exchange=broker_config.STATUS_EXCHANGE,
            properties=BasicProperties(
                headers=status_header,
                correlation_id=request_id),
            routing_key=self.worker_name,
            body=body
        )

    def _confirm_request(self, request_id, body, delivery_tag, message=None):
        self.request_channel.basic_ack(delivery_tag=delivery_tag)
        self._update_status(request_id, body, broker_config.ACTION_REQUEST_SUCCESS, message)

    def _reject_request(self, request_id, body, delivery_tag, message=None):
        self.request_channel.basic_reject(delivery_tag=delivery_tag, requeue=False)
        self._update_status(request_id, body, broker_config.ACTION_REQUEST_FAIL, message)
