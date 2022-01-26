import json
from logging import getLogger
from threading import Thread

from pika import BasicProperties

from std_daq_service.broker.common import BrokerClientBase, STATUS_EXCHANGE, REQUEST_EXCHANGE, KILL_EXCHANGE, \
    ACTION_REQUEST_START, ACTION_REQUEST_SUCCESS, ACTION_REQUEST_FAIL

_logger = getLogger("BrokerService")


class PrimaryBrokerService(BrokerClientBase):
    def __init__(self, broker_url, service_name, tag="#", request_callback=None, kill_callback=None):
        super().__init__(broker_url=broker_url, tag=tag)

        self.service_name = service_name
        _logger.info(f"Service {service_name} starting.")

        self.bind_queue(REQUEST_EXCHANGE, self.tag, self._request_callback, False)
        self.bind_queue(KILL_EXCHANGE, self.tag, self._kill_callback, True)

        self.user_request_callback = request_callback
        self.user_kill_callback = kill_callback

        self.start()

    def _request_callback(self, channel, method_frame, header_frame, body):

        if self.user_request_callback is None:
            return

        request_id = header_frame.correlation_id
        delivery_tag = method_frame.delivery_tag
        _logger.info(f"Received request_id {request_id} with delivery_tag {delivery_tag}.")

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
                result = self.user_request_callback(request_id, request)

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
