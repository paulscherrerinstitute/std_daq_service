import argparse
import logging
from time import sleep

import bitshuffle
import numpy as np
from std_buffer.image_metadata_pb2 import ImageMetadata
import zmq
from zmq import Again

from std_daq_service.config import load_daq_config
from std_daq_service.image_simulator.start import N_RAM_BUFFER_SLOTS
from std_daq_service.ram_buffer import RamBuffer

_logger = logging.getLogger("Compression")


def start_compression(config_file):
    daq_config = load_daq_config(config_file)
    detector_name = daq_config['detector_name']
    image_n_bytes = daq_config['bit_depth'] * daq_config['image_pixel_height'] * daq_config['image_pixel_width']

    image_metadata_address = f"ipc:///tmp/{detector_name}-compressed"

    # Receive the image metadata stream from the detector.
    ctx = zmq.Context()
    image_metadata_receiver = ctx.socket(zmq.SUB)
    image_metadata_receiver.setsockopt(zmq.CONFLATE, 1)
    image_metadata_receiver.connect(image_metadata_address)
    image_metadata_receiver.setsockopt_string(zmq.SUBSCRIBE, "")

    buffer = RamBuffer(channel_name=detector_name, data_n_bytes=image_n_bytes, n_slots=N_RAM_BUFFER_SLOTS,
                       compression=True)

    image_meta = ImageMetadata()
    while True:
        try:
            meta_raw = image_metadata_receiver.recv(flags=zmq.NOBLOCK)
            if meta_raw:
                image_meta.ParseFromString(meta_raw)

                compressed_data = buffer.get_data(image_meta.image_id)
                data = bitshuffle.decompress_lz4(np.array(compressed_data),
                                                 shape=[image_meta.height, image_meta.width],
                                                 dtype='uint16')

                print(data)

            sleep(1)
        except Again:
            sleep(1)
        except KeyboardInterrupt:
            break
        except Exception:
            _logger.exception("Error in validator loop.")
            raise


def main():
    parser = argparse.ArgumentParser(description='Stream compression')
    parser.add_argument("config_file", type=str, help="Path to the config file managed by this instance.")

    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)

    start_compression(config_file=args.config_file)


if __name__ == "__main__":
    main()
