import argparse
import logging
import os

from std_daq_service.broker.postprocessing_service import PostprocessingBrokerService
from std_daq_service.broker.primary_service import PrimaryBrokerService
from std_daq_service.epics_validator.service import EpicsValidationService
from std_daq_service.epics_writer.service import EpicsWriterService
from std_daq_service.start_utils import default_service_setup

_logger = logging.getLogger("EpicsWriter")


def main():
    parser = argparse.ArgumentParser(description='Epics buffer writer service')
    parser.add_argument("--broker_url", type=str, help="Host of broker instance.",
                        default=os.environ.get("BROKER_HOST", '127.0.0.1'))
    parser.add_argument("--tag", type=str, help="Tag of the Epics writer to validate", default="#.epics_writer")
    service_name, config, args = default_service_setup(parser)

    broker_url = args.broker_url
    primary_tag = args.tag

    _logger.info(f'Epics validator {service_name} listening on broker {broker_url} '
                 f'for primary service {primary_tag}.')

    service = EpicsValidationService()

    listener = PostprocessingBrokerService(broker_url=broker_url,
                                           service_name=service_name,
                                           primary_tag=primary_tag,
                                           request_callback=service.on_request,
                                           kill_callback=service.on_kill)


    try:
        listener.block()
    except KeyboardInterrupt:
        pass

    listener.stop()

    _logger.info(f'Service {args.service_name} stopping.')


if __name__ == "__main__":
    main()
