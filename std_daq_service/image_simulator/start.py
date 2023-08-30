import argparse
import numpy as np
import json
import logging

import zmq
from tifffile import tifffile

from std_daq_service.ram_buffer import RamBuffer
from std_daq_service.rest_v2.utils import set_ipc_rights
from std_buffer.image_metadata_pb2 import ImageMetadata, ImageMetadataStatus, GFImageMetadata, JFImageMetadata, EGImageMetadata

_logger = logging.getLogger(__name__)

N_RAM_BUFFER_SLOTS = 10000


def generate_default_image():
    pass


def main():
    parser = argparse.ArgumentParser(description='ImageMetadata source simulator')
    parser.add_argument('detector_config_file', type=str, help='JSON file with detector configuration.')
    parser.add_argument('-r', '--rep_rate', type=int, help='Repetition rate of the stream.', default=10)
    parser.add_argument('-f', '--file', type=str, default=None, help='Image in TIFF format to stream.')

    args = parser.parse_args()
    rep_rate = args.rep_rate
    image_filename = args.file

    with open(args.detector_config_file, 'r') as input_file:
        config = json.load(input_file)

    detector_name = config['detector_name']
    detector_type = config['detector_type']
    image_height = config['image_pixel_height']
    image_width = config['image_pixel_width']
    bit_depth = config['bit_depth']
    image_n_bytes = image_width * image_height * (bit_depth // 8)

    _logger.info(f'Starting simulated source with rep_rate {rep_rate} and image_shape {(image_height, image_width)} '
                 f'for source_id {detector_name}')

    if image_filename:
        _logger.info(f'Loading image {image_filename}')
        image = tifffile.imread(image_filename)
        image = np.multiply(image, (2 ** bit_depth) / image.max(), casting='unsafe').astype(f'uint{bit_depth}')
    else:
        image = np.random.randint(low=0, high=(2**bit_depth)-1, size=(image_height, image_width),
                                  dtype=f'uint{bit_depth}')
    image_bytes = image.to_bytes()

    meta = ImageMetadata()
    meta.height = image_height
    meta.width = image_width
    meta.dtype = bit_depth // 8
    meta.status = ImageMetadataStatus.good_image

    # Set the appropriate metadata depending on the detector name
    if detector_type == 'gigafrost':
        meta.gf = GFImageMetadata()
    elif detector_type == 'jungfrau':
        meta.jf = JFImageMetadata()  # set JFImageMetadata fields her
    elif detector_type == 'eiger':
        meta.eg = EGImageMetadata()
    else:
        raise ValueError(f'Unknown detector type: {detector_type}')

    metadata_address = f"ipc:///tmp/{detector_name}-image"
    _logger.info(f'Binding to {metadata_address}')
    metadata_sender = zmq.Context().socket(zmq.PUB)
    metadata_sender.bind(metadata_address)
    set_ipc_rights(metadata_address)

    ram_buffer = RamBuffer(channel_name=detector_name, data_n_bytes=image_n_bytes, n_slots=N_RAM_BUFFER_SLOTS)

    i_image = 0
    try:
        _logger.info("Sending images...")
        while True:
            meta.image_id = i_image

            ram_buffer.write(i_image, image_bytes)
            metadata_sender.send(meta.SerializeToString())

            i_image += 1
    except KeyboardInterrupt:
        pass

    _logger.info('Simulated image stream stopped.')


if __name__ == '__main__':
    main()
