import argparse
import logging
import os
from time import sleep

import bitshuffle
import bitshuffle.h5
import h5py
import numpy as np
from std_buffer.image_metadata_pb2 import ImageMetadata
import zmq
from zmq import Again

from std_daq_service.config import load_daq_config
from std_daq_service.image_simulator.start import N_RAM_BUFFER_SLOTS
from std_daq_service.ram_buffer import RamBuffer

_logger = logging.getLogger("Compression")


def start_writing(config_file, output_file, n_images):
    daq_config = load_daq_config(config_file)
    detector_name = daq_config['detector_name']
    image_n_bytes = daq_config['bit_depth'] * daq_config['image_pixel_height'] * daq_config['image_pixel_width']

    image_metadata_address = f"ipc:///tmp/{detector_name}-image"

    # Receive the image metadata stream from the detector.
    ctx = zmq.Context()
    image_metadata_receiver = ctx.socket(zmq.SUB)
    # image_metadata_receiver.setsockopt(zmq.CONFLATE, 1)
    image_metadata_receiver.connect(image_metadata_address)
    image_metadata_receiver.setsockopt_string(zmq.SUBSCRIBE, "")

    buffer = RamBuffer(channel_name=detector_name, data_n_bytes=image_n_bytes, n_slots=N_RAM_BUFFER_SLOTS)

    image_meta = ImageMetadata()

    os.seteuid(daq_config['writer_user_id'])
    file = h5py.File(output_file, 'w')
    # block_size = 0 let Bitshuffle choose its value
    block_size = 0
    image_shape = [daq_config['image_pixel_height'], daq_config['image_pixel_width']]
    dataset = file.create_dataset(detector_name,
                                  tuple([n_images] + image_shape),
                                  compression=bitshuffle.h5.H5FILTER,
                                  compression_opts=(block_size, bitshuffle.h5.H5_COMPRESS_LZ4),
                                  dtype=f'uint{daq_config["bit_depth"]}',
                                  chunks=tuple([1] + image_shape)
                                  )

    i_image = 0
    while True:
        try:
            meta_raw = image_metadata_receiver.recv(flags=zmq.NOBLOCK)
            if meta_raw:
                image_meta.ParseFromString(meta_raw)

                dataset[i_image] = buffer.get_data(image_meta.image_id)
                i_image += 1

            sleep(1)
        except Again:
            sleep(1)
        except KeyboardInterrupt:
            break
        except Exception:
            _logger.exception("Error in validator loop.")
            break
        finally:
            file.close()

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
