import logging
import os
import re
import stat
from collections import OrderedDict
from time import time_ns

from std_buffer.image_metadata_pb2 import ImageMetadata, ImageMetadataDtype

import cv2
import numpy as np
import zmq

DAQ_CONFIG_FIELDS = ['detector_name', 'detector_type',
                     'bit_depth', 'image_pixel_height', 'image_pixel_width', 'n_modules', 'start_udp_port',
                     'writer_user_id', 'module_positions']

DAQ_CONFIG_INT_FIELDS = ['bit_depth', 'image_pixel_height', 'image_pixel_width', 'n_modules', 'start_udp_port',
                         'writer_user_id']


_logger = logging.getLogger("utils")


def get_image_n_bytes(image_meta: ImageMetadata):
    dtype_to_bytes = {
        'uint8': 1, 'int8': 1,
        'uint16': 2, 'int16': 2,
        'uint32': 4, 'int32': 4, 'float32': 24,
        'uint64': 8, 'int64': 8, 'float64': 8
    }

    image_n_bytes = image_meta.width * image_meta.height * (dtype_to_bytes[ImageMetadataDtype.Name(image_meta.dtype)])
    return image_n_bytes


def validate_output_file(output_file, user_id):
    try:
        # Set user_id for checking the directory permissions.
        if user_id > 0:
            _logger.info(f"Setting effective user_id to {user_id}.")
            os.seteuid(user_id)
        else:
            _logger.info(f"Using process user_id.")

        path_folder = os.path.dirname(output_file)
        if not os.path.exists(path_folder):
            raise RuntimeError(f'Output file folder {path_folder} does not exist. Please create it first.')
    finally:
        # In case you set the user_id, revert back to original.
        if user_id > 0:
            _logger.info(f"Returning effective user_id to {os.getuid()}.")
            os.seteuid(os.getuid())


def update_config(old_config, config_updates):
    if old_config is not None:
        new_config = OrderedDict({param: config_updates.get(param, old_config[param])
                                  for param in DAQ_CONFIG_FIELDS})
    else:
        new_config = config_updates

    validate_config(new_config)

    return new_config


def validate_config(new_config):
    error_message = ""
    for field_name in DAQ_CONFIG_FIELDS:
        if field_name not in new_config:
            error_message += f' missing {field_name},'
        elif field_name in DAQ_CONFIG_INT_FIELDS:
            try:
                new_config[field_name] = int(new_config[field_name])
            except ValueError:
                error_message += f' non-int value {field_name};'

    if error_message:
        raise RuntimeError(f"Config errors:{error_message}")


def generate_mjpg_image_stream(ctx, image_stream_url):
    socket = ctx.socket(zmq.SUB)
    socket.setsockopt(zmq.SUBSCRIBE, b'')
    socket.connect(image_stream_url)

    while True:
        json_header = socket.recv_json()
        image_bytes = socket.recv()

        image_width = json_header['width']
        image_height = json_header['height']
        dtype = json_header['dtype']

        # interpret the byte array as a NumPy array
        image_array = np.frombuffer(image_bytes, dtype=dtype).reshape(image_height, image_width)

        # convert the uint16 grayscale image to uint8 (0-255)
        image_array = (image_array // 256).astype(np.uint8)
        image_array = cv2.resize(image_array, (640, 480))
        image_array = cv2.applyColorMap(image_array, cv2.COLORMAP_JET)

        # encode the color image as JPEG
        _, buffer = cv2.imencode('.jpg', image_array)
        image_bytes = buffer.tobytes()

        # yield the frame for the MJPG stream
        yield b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + image_bytes + b'\r\n'


def set_ipc_rights(ipc_path):
    if ipc_path.startswith("ipc://"):
        filename = ipc_path[6:]
        current_p = os.stat(filename).st_mode
        additional_p = stat.S_IWGRP | stat.S_IWOTH
        _logger.info(f"Relax permission on {filename}.")
        os.chmod(filename, current_p | additional_p)
