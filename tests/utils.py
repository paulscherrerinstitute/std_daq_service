from time import sleep

from pika import BlockingConnection, ConnectionParameters

from sf_daq_service.common import broker_config


def get_test_broker():
    connection = BlockingConnection(ConnectionParameters(broker_config.TEST_BROKER_URL))
    channel = connection.channel()

    channel.exchange_declare(exchange=broker_config.REQUEST_EXCHANGE,
                             exchange_type=broker_config.REQUEST_EXCHANGE_TYPE)
    channel.exchange_declare(exchange=broker_config.STATUS_EXCHANGE,
                             exchange_type=broker_config.STATUS_EXCHANGE_TYPE)

    queue = channel.queue_declare(queue="", exclusive=True).method.queue
    channel.queue_bind(queue=queue,
                       exchange=broker_config.STATUS_EXCHANGE)

    sleep(0.1)

    return channel, queue
