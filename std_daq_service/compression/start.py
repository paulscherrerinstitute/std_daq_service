import argparse
import logging
from time import sleep, time

import bitshuffle
import numpy as np
from std_buffer.image_metadata_pb2 import ImageMetadata
import zmq
from zmq import Again

from std_daq_service.config import load_daq_config
from std_daq_service.ram_buffer import RamBuffer

_logger = logging.getLogger("Compression")


def start_compression(config_file):
    daq_config = load_daq_config(config_file)
    detector_name = daq_config['detector_name']
    shape = [daq_config['image_pixel_height'], daq_config['image_pixel_width']]
    dtype = f'uint{daq_config["bit_depth"]}'
    image_n_bytes = int(daq_config['bit_depth'] / 8 *
                        daq_config['image_pixel_height'] * daq_config['image_pixel_width'])
    block_size = 0

    image_metadata_address = f"ipc:///tmp/{detector_name}-image"

    # Receive the image metadata stream from the detector.
    ctx = zmq.Context()
    image_metadata_receiver = ctx.socket(zmq.SUB)
    image_metadata_receiver.connect(image_metadata_address)
    image_metadata_receiver.setsockopt_string(zmq.SUBSCRIBE, "")
    image_metadata_receiver.setsockopt(zmq.RCVTIMEO, 200)

    buffer = RamBuffer(channel_name=detector_name, shape=shape, dtype=dtype,
                       data_n_bytes=image_n_bytes, n_slots=1000)

    image_meta = ImageMetadata()
    compressed_bytes = 0
    uncompressed_bytes = 0
    n_compressions = 0
    start_time = time()
    while True:
        try:
            meta_raw = image_metadata_receiver.recv()
            image_meta.ParseFromString(meta_raw)

            data = buffer.get_data(image_meta.image_id)
            uncompressed_bytes += data.nbytes

            compressed_data = bitshuffle.compress_lz4(data, block_size)
            compressed_bytes += compressed_data.nbytes

            end_time = time()
            if end_time - start_time > 1:
                start_time = end_time

                print(f'Uncompressed {uncompressed_bytes/1024/1024} MB/s; '
                      f'Compressed {compressed_bytes/1024/1024} MB/s; '
                      f'Ratio {compressed_bytes/uncompressed_bytes}; '
                      f'Frequency {n_compressions} Hz')
                uncompressed_bytes = 0
                compressed_bytes = 0
                n_compressions = 0

        except Again:
            continue
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
