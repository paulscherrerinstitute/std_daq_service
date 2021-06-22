import uuid
from logging import getLogger
from threading import Thread

from pika import BlockingConnection, ConnectionParameters

_logger = getLogger("broker_utils")

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


class BrokerClientBase(object):
    def __init__(self, broker_url, tag):
        self.tag = tag

        self.connection = BlockingConnection(ConnectionParameters(broker_url))
        self.channel = self.connection.channel()
        self.channel.basic_qos(prefetch_count=1)

        self.channel.exchange_declare(exchange=REQUEST_EXCHANGE, exchange_type=REQUEST_EXCHANGE_TYPE)
        self.channel.exchange_declare(exchange=STATUS_EXCHANGE, exchange_type=STATUS_EXCHANGE_TYPE)
        self.channel.exchange_declare(exchange=KILL_EXCHANGE, exchange_type=KILL_EXCHANGE_TYPE)

        self.thread = None

        _logger.info(f"Setup client with tag {tag} on broker_url {broker_url}.")

    def start(self):
        if self.thread is not None:
            raise RuntimeError("Client already started.")

        def start_consuming():
            try:
                self.channel.start_consuming()
            except KeyboardInterrupt:
                self.channel.stop_consuming()

        self.thread = Thread(target=start_consuming)
        self.thread.start()

    def stop(self):
        _logger.info("Stopping connection.")

        self.connection.add_callback_threadsafe(self.channel.stop_consuming)
        self.thread.join()

    def bind_queue(self, exchange, tag, callback, auto_ack):
        queue = str(uuid.uuid4())

        _logger.info(f"Binding queue {queue} to exchange {exchange} with tag {tag}.")

        self.channel.queue_declare(queue, auto_delete=True, exclusive=True)
        self.channel.queue_bind(queue=queue,
                                exchange=exchange,
                                routing_key=tag)

        self.channel.basic_consume(queue, callback, auto_ack=auto_ack)

    def block(self):
        self.thread.join()
