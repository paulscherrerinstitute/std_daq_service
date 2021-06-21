import uuid
from logging import getLogger

_logger = getLogger("broker_utils")


def bind_queue_to_exchange(channel, exchange, tag, callback, auto_ack):
    queue = str(uuid.uuid4())

    _logger.info(f"Binding queue {queue} to exchange {exchange} with tag {tag}.")

    channel.queue_declare(queue, auto_delete=True, exclusive=True)
    channel.queue_bind(queue=queue,
                       exchange=exchange,
                       routing_key=tag)

    channel.basic_consume(queue, callback, auto_ack=auto_ack)
