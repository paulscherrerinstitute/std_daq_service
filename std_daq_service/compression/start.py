import argparse
import logging
from std_buffer.image_metadata_pb2 import ImageMetadata
import zmq

from std_daq_service.config import load_daq_config
from std_daq_service.ram_buffer import RamBuffer

_logger = logging.getLogger("Compression")


def start_compression(config_file):
    daq_config = load_daq_config(config_file)
    image_metadata_address = "ipc:///tmp/metadata"
    detector_name = 'test_detector'
    image_n_bytes = 512 * 1024 * 2 * 16
    N_RAM_BUFFER_SLOTS = 10000

    # Receive the image metadata stream from the detector.
    ctx = zmq.Context()
    image_metadata_receiver = ctx.socket(zmq.SUB)
    image_metadata_receiver.connect(image_metadata_address)

    buffer = RamBuffer(channel_name=detector_name, data_n_bytes=image_n_bytes, n_slots=N_RAM_BUFFER_SLOTS)

    image_meta = ImageMetadata()
    while True:
        try:
            meta_raw = image_metadata_receiver.recv(flags=zmq.NOBLOCK)
            image_meta.ParseFromString(meta_raw)

            uncompressed_data = buffer.get_data(image_meta.image_id)

            # compressed_data....

            buffer.write(image_meta.image_id, compressed_data)

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