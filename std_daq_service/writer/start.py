import argparse
import logging
import os
from time import sleep, time

import bitshuffle
import bitshuffle.h5
import h5py
import numpy as np
from std_buffer.image_metadata_pb2 import ImageMetadata
import zmq
from zmq import Again

from std_daq_service.config import load_daq_config
from std_daq_service.ram_buffer import RamBuffer

_logger = logging.getLogger("Compression")


def start_writing(config_file, output_file, n_images):
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
    # image_metadata_receiver.setsockopt(zmq.CONFLATE, 1)
    image_metadata_receiver.connect(image_metadata_address)
    image_metadata_receiver.setsockopt_string(zmq.SUBSCRIBE, "")

    buffer = RamBuffer(channel_name=detector_name, shape=shape, dtype=dtype,
                       data_n_bytes=image_n_bytes, n_slots=1000)

    image_meta = ImageMetadata()
    try:
        os.seteuid(daq_config['writer_user_id'])
        # Initialize HDF5 file and dataset here.
        with h5py.File(output_file, 'w') as file:
            dataset = file.create_dataset(detector_name, tuple([n_images] + shape),
                                          # compression=bitshuffle.h5.H5FILTER,
                                          # compression_opts=(block_size, bitshuffle.h5.H5_COMPRESS_LZ4),
                                          dtype=dtype, chunks=tuple([1] + shape))

            i_image = 0
            start_time = time()
            while True:
                if i_image == n_images:
                    break

                if time() - start_time > 1:
                    start_time = time()
                    print(i_image)

                try:
                    meta_raw = image_metadata_receiver.recv(flags=zmq.NOBLOCK)
                    if meta_raw:
                        image_meta.ParseFromString(meta_raw)
                        data = buffer.get_data(image_meta.image_id)
                        dataset.id.write_direct_chunk((i_image, 0, 0), data)
                        i_image += 1

                except Again:
                    continue
                except KeyboardInterrupt:
                    break
                except Exception:
                    _logger.exception("Error in validator loop.")
                    break
    except Exception as e:
        _logger.exception(f"Failed to write to file: {e}")
    finally:
        os.seteuid(0)


def main():
    parser = argparse.ArgumentParser(description='Stream writer')
    parser.add_argument("config_file", type=str, help="Path to the config file managed by this instance.")
    parser.add_argument("output_file", type=str, help="Absolute path filename to write the data to.")
    parser.add_argument("n_images", type=int, help="Number of images to write.")

    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)

    start_writing(config_file=args.config_file, output_file=args.output_file, n_images=args.n_images)


if __name__ == "__main__":
    main()
