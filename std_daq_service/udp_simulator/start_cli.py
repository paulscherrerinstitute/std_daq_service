import argparse
import json
import logging

from std_daq_service.udp_simulator.udp_stream import generate_udp_stream
from std_daq_service.udp_simulator.util import get_detector_generator

_logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description='Detector UDP stream generator')
    parser.add_argument('detector_config_file', type=str, help='JSON file with detector configuration.')
    parser.add_argument('output_ip', type=str, help='IP to send the UPD packets to.')
    parser.add_argument('-r', '--rep_rate', type=int, help='Repetition rate of the stream.', default=10)
    parser.add_argument('-n', '--n_images', type=int, default=None, help='Number of images to generate.')
    parser.add_argument('-f', '--file', type=str, default=None, help='Image in TIFF format to stream.')

    args = parser.parse_args()
    output_ip = args.output_ip
    rep_rate = args.rep_rate
    n_images = args.n_images
    image_filename = args.file

    with open(args.detector_config_file, 'r') as input_file:
        config = json.load(input_file)

    detector_type = config['detector_type']
    image_height = config['image_pixel_height']
    image_width = config['image_pixel_width']
    bit_depth = config['bit_depth']
    n_modules = config['n_modules']
    modules_info = config.get('submodule_info', None)

    generator = get_detector_generator(detector_type, image_height, image_width, bit_depth, n_modules, modules_info, image_filename=image_filename)

    _logger.info(f'Starting simulated {config["detector_type"]} with rep_rate {rep_rate} on {output_ip} '
                 f'with start_udp_port {config["start_udp_port"]} with image_shape {(image_height, image_width)} '
                 f'for {"unlimited" if n_images is None else n_images} images.')

    try:
        generate_udp_stream(generator, output_ip, config['start_udp_port'], rep_rate, n_images)
    except KeyboardInterrupt:
        pass

    print('Simulated udp stream stopped.')


if __name__ == '__main__':
    main()
