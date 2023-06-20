import argparse
import logging
import os

import cv2
import h5py as h5py
import numpy as np
import redis
import json
import imageio
from io import BytesIO

from std_daq_service.rest_v2.redis_storage import StdDaqRedisStorage

_logger = logging.getLogger("FileValidator")

REDIS_BLOCK_TIMEOUT = 500
N_GIF_IMAGES = 5


def create_gif(data, n_images):
    total_images = data.shape[0]
    selected_indices = np.linspace(0, total_images-1, n_images).astype(int)
    images = []

    for idx in selected_indices:
        # Extract and normalize the image
        image = data[idx][:]
        image -= np.min(image)
        image *= (255.0 / np.max(image))
        image = image.astype(np.uint8)

        # Resize image to 256x256 using OpenCV
        img_resized = cv2.resize(image, (256, 256))
        images.append(img_resized)

    byte_object = BytesIO()
    imageio.mimsave(byte_object, images, 'GIF', duration=1)
    return byte_object.getvalue()


def validate_file(log, user_id, detector_name):
    # TODO: Detector name should be in the write request.
    source_id = detector_name
    output_file = log['info']['output_file']

    readable = False
    n_images = None
    image_id_range = None

    try:
        # Switch to writer user.
        if user_id > 0:
            _logger.info(f'Switching to user_id {user_id}.')
            os.seteuid(user_id)
        else:
            _logger.info(f'Keeping original user_id.')

        with h5py.File(output_file, 'r') as out_f:
            readable = True
            data_shape = out_f[source_id]['data'].shape

            n_images = data_shape[0]
            image_id_range = [out_f[source_id]['image_id'][0], out_f[source_id]['image_id'][-1]]

            gif_bytes = create_gif(out_f[source_id]['data'], N_GIF_IMAGES)
    finally:
        # Switch back to original process user.
        if user_id > 0:
            _logger.info(f'Switching back to user_id {os.getuid()}')
            os.seteuid(os.getuid())

    return {
        'readable': readable,
        'n_images': n_images,
        'image_id_range': image_id_range
    }, gif_bytes


def start_validator(config_file, redis_url):
    _logger.info(f"Starting file validator for config {config_file} and Redis {redis_url}.")

    redis_host, redis_port = redis_url.split(':')
    redis_client = redis.Redis(host=redis_host, port=redis_port)
    storage = StdDaqRedisStorage(redis=redis_client)

    with open(config_file, 'r') as input_file:
        daq_config = json.load(input_file)
    writer_user_id = daq_config['writer_user_id']
    detector_name = daq_config['detector_name']

    last_log_id = '$'
    while True:
        try:
            response = redis.xread({"daq:log": last_log_id}, block=REDIS_BLOCK_TIMEOUT)
            if not response:
                continue

            last_log_id, status = response[0][0].decode(), json.loads(response[0][1][b'json'])

            report, gif_bytes = validate_file(status, writer_user_id, detector_name)
            _logger.info(f"File {status['info']['output_file']} validated: {report}.")

            storage.add_report(last_log_id, {
                'report_type': 'file_validator',
                'report': report
            })

            storage.add_gif(last_log_id, gif_bytes)

        except KeyboardInterrupt:
            break
        except Exception:
            _logger.exception("Error in validator loop.")
            raise

    redis_client.close()
    _logger.info("Shutting down validator.")


def main():
    parser = argparse.ArgumentParser(description='User file validator')
    parser.add_argument("config_file", type=str, help="Path to the config file managed by this instance.")
    parser.add_argument('--redis_url', default="0.0.0.0:6379", help="Redis instance url in format '0.0.0.0:6379'")

    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)

    start_validator(config_file=args.config_file, redis_url=args.redis_url)


if __name__ == "__main__":
    main()
