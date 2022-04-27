import argparse
import logging
import os

from std_daq_service.broker.primary_service import PrimaryBrokerService
from std_daq_service.epics_writer.service import EpicsWriterService
from std_daq_service.start_utils import default_service_setup

_logger = logging.getLogger("EpicsWriter")


def start_epics_writer(service_name, broker_url, redis_host, redis_port, tag):
    _logger.info(f'Epics buffer writer {service_name} listening on broker {broker_url} on buffer {redis_host}.')

    service = EpicsWriterService(redis_host=redis_host, redis_port=redis_port)

    listener = PrimaryBrokerService(broker_url=broker_url,
                                    service_name=service_name,
                                    tag=tag,
                                    request_callback=service.on_request,
                                    kill_callback=service.on_kill)

    return service, listener


def main():
    parser = argparse.ArgumentParser(description='Epics buffer writer service')
    parser.add_argument("--broker_url", type=str, help="Host of broker instance.",
                        default=os.environ.get("BROKER_HOST", '127.0.0.1'))
    parser.add_argument("--redis_host", type=str, help="Host of redis instance.",
                        default=os.environ.get("REDIS_HOST", "localhost"))
    parser.add_argument("--redis_port", type=int, help='Port of redis instance',
                        default=os.environ.get("REDIS_PORT", 6379))
    parser.add_argument("--tag", type=str, help="Tag to listen for on the broker",
                        default="#")
    service_name, config, args = default_service_setup(parser)

    broker_url = args.broker_url
    redis_host = args.redis_host
    redis_port = args.redis_port
    tag = args.tag

    service, listener = start_epics_writer(service_name, broker_url, redis_host, redis_port, tag)

    try:
        listener.block()
    except KeyboardInterrupt:
        pass

    listener.stop()
    _logger.info(f'Service {args.service_name} stopping.')


if __name__ == "__main__":
    main()
