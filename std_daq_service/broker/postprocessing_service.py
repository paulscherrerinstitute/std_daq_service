import json
from logging import getLogger
from threading import Thread

from pika import BasicProperties

from std_daq_service.broker.common import BrokerClientBase, STATUS_EXCHANGE, KILL_EXCHANGE, \
    ACTION_REQUEST_START, ACTION_REQUEST_SUCCESS, ACTION_REQUEST_FAIL

_logger = getLogger("BrokerPostprocessingService")


class PostprocessingBrokerService(BrokerClientBase):
    def __init__(self, broker_url, service_name, primary_tag, tag="#", status_callback=None, kill_callback=None):
        super().__init__(broker_url=broker_url, tag=tag)

        self.service_name = service_name
        self.primary_tag = primary_tag
        _logger.info(f"Service {service_name} starting.")

        self.bind_queue(STATUS_EXCHANGE, self.primary_tag, self._status_callback, False)
        self.bind_queue(KILL_EXCHANGE, self.tag, self._kill_callback, True)

        self.user_status_callback = status_callback
        self.user_kill_callback = kill_callback

        self.start()

    def _status_callback(self, channel, method_frame, header_frame, body):

        request_id = header_frame.correlation_id
        delivery_tag = method_frame.delivery_tag
        primary_message = header_frame.headers["message"]
        _logger.info(f"Received request_id {request_id} with input file {primary_message}.")

        # Drop message through if user did not specify a status callback.
        if self.user_status_callback is None:
            channel.basic_ack(delivery_tag=delivery_tag)
            return

        # Check if source is the one we are listening for.
        source = header_frame.headers["source"]
        if source != self.primary_tag:
            _logger.debug(f"Source {source} and primary_tag {self.primary_tag} do not match. Skipping message.")
            channel.basic_ack(delivery_tag=delivery_tag)
            return

        action = header_frame.headers["action"]

        # Skip start action of service.
        if action == ACTION_REQUEST_START:
            channel.basic_ack(delivery_tag=delivery_tag)
            return

        # If the primary service failed, this one will as well.
        if action == ACTION_REQUEST_FAIL:
            self.channel.basic_publish(STATUS_EXCHANGE, self.tag, body, BasicProperties(
                correlation_id=request_id, headers={
                    'action': ACTION_REQUEST_FAIL,
                    'source': self.service_name,
                    'message': f"Primary service {self.primary_tag} failure. "
                }))

            channel.basic_ack(delivery_tag=delivery_tag)
            return

        request = json.loads(body.decode())
        _logger.debug(f"Received request {request}")

        self.channel.basic_publish(STATUS_EXCHANGE, self.tag, body, BasicProperties(
            correlation_id=request_id, headers={
                'action': ACTION_REQUEST_START,
                'source': self.service_name,
                'message': None
            }))

        def request_f():
            try:
                result = self.user_status_callback(request_id, request)

                def confirm():
                    self.channel.basic_publish(STATUS_EXCHANGE, self.tag, body, BasicProperties(
                        correlation_id=request_id, headers={
                            'action': ACTION_REQUEST_SUCCESS,
                            'source': self.service_name,
                            'message': result
                        }))

                    channel.basic_ack(delivery_tag=delivery_tag)

                self.connection.add_callback_threadsafe(confirm)

            except Exception as e:
                _logger.exception("Error while executing user_request_callback.")

                error_message = str(e)

                def reject():
                    self.channel.basic_publish(STATUS_EXCHANGE, self.tag, body, BasicProperties(
                        correlation_id=request_id, headers={
                            'action': ACTION_REQUEST_FAIL,
                            'source': self.service_name,
                            'message': error_message
                        }))
                    self.channel.basic_reject(delivery_tag=delivery_tag, requeue=False)

                self.connection.add_callback_threadsafe(reject)

        thread = Thread(target=request_f)
        thread.daemon = True
        thread.start()

    def _kill_callback(self, channel, method_frame, header_frame, body):

        if self.user_kill_callback is None:
            pass

        request_id = header_frame.correlation_id
        _logger.info(f"Received kill for request_id {request_id}.")

        self.user_kill_callback(request_id)
