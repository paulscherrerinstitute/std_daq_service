import argparse
import logging
from time import sleep

import bitshuffle
import cv2
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
    image_n_bytes = int(daq_config['bit_depth'] * daq_config['image_pixel_height'] * daq_config['image_pixel_width'] / 8)

    image_metadata_address = f"ipc:///tmp/{detector_name}-compressed"

    # Receive the image metadata stream from the detector.
    ctx = zmq.Context()
    image_metadata_receiver = ctx.socket(zmq.SUB)
    image_metadata_receiver.setsockopt(zmq.CONFLATE, 1)
    image_metadata_receiver.connect(image_metadata_address)
    image_metadata_receiver.setsockopt_string(zmq.SUBSCRIBE, "")

    buffer = RamBuffer(channel_name=detector_name, data_n_bytes=image_n_bytes, n_slots=1000,
                       compression=True)

    image_meta = ImageMetadata()
    while True:
        written = False
        try:
            meta_raw = image_metadata_receiver.recv(flags=zmq.NOBLOCK)
            if meta_raw:
                image_meta.ParseFromString(meta_raw)

                compressed_data = buffer.get_data(image_meta.image_id, (image_meta.size,), 'uint8')
                data = bitshuffle.decompress_lz4(compressed_data,
                                                 shape=(image_meta.height, image_meta.width),
                                                 dtype=np.dtype('uint16'))

                # Scale image to 8 bits with full range.
                min_val = data.min()
                max_val = data.max() or 1

                frame = ((data - min_val) * (255.0 / (max_val - min_val))).clip(0, 255).astype(np.uint8)
                frame = cv2.flip(frame, 0)
                image = cv2.resize(frame, (800, 600))
                # apply a color scheme to the grayscale image
                image = cv2.applyColorMap(image, cv2.COLORMAP_HOT)

                _, buffer = cv2.imencode('.jpg', image)
                image_bytes = buffer.tobytes()
                if not written:
                    with open('output.jpg', 'bw') as output_file:
                        output_file.write(image_bytes)
                    written = True

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
