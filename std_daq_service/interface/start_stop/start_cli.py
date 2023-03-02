import argparse

import json
import logging

from std_daq_service.interface.start_stop.utils import get_stream_addresses
from std_daq_service.udp_simulator.generator.gigafrost import GFUdpPacketGenerator
from std_daq_service.udp_simulator.generator.udp_stream import generate_udp_stream

_logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description='Start detector acquisition.')
    parser.add_argument('detector_config_file', type=str, help='JSON file with detector configuration.')
    parser.add_argument('n_images', type=int, help='Number of images to write. 0 for unlimited / until CTRL+C.')
    parser.add_argument('output_file', type=str, help='Absolute output path of H5 file.')

    args = parser.parse_args()
    n_images = args.n_images
    output_file = args.output_file

    with open(args.detector_config_file, 'r') as input_file:
        config = json.load(input_file)

    detector_name = config['detector_name']
    image_metadata_stream, writer_control_stream, writer_status_stream = get_stream_addresses(detector_name)


if __name__ == '__main__':
    main()
