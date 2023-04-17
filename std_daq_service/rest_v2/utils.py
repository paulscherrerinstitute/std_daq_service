import os
import re
from collections import OrderedDict

import cv2
import numpy as np
import zmq

DAQ_CONFIG_FIELDS = ['detector_name', 'detector_type', 'bit_depth',
                     'image_pixel_height', 'image_pixel_width', 'n_modules', 'start_udp_port']


def get_parameters_from_write_request(json_request):
    if 'output_file' not in json_request:
        raise RuntimeError(f'Mandatory field missing: output_file')

    output_file = json_request.get('output_file')
    validate_output_file(output_file)

    n_images_str = json_request.get('n_images')
    n_images = validate_n_images(n_images_str)

    return output_file, n_images


def validate_output_file(output_file):
    if output_file is None:
        raise RuntimeError(f'Mandatory field missing: output_file')

    if not output_file.startswith('/'):
        raise RuntimeError(f'Invalid output_file={output_file}. Path must be absolute - starts with "/".')

    path_validator = '\/[a-zA-Z0-9_\/-]*\..+[^\/]$'
    if not re.compile(path_validator).match(output_file):
        raise RuntimeError(f'Invalid output_file={output_file}. Must be a valid posix path.')

    path_folder = os.path.dirname(output_file)
    if not os.path.exists(path_folder):
        raise RuntimeError(f'Output file folder {path_folder} does not exist. Please create it first.')


def validate_n_images(n_images_str):
    if n_images_str is None:
        raise RuntimeError(f'Mandatory field missing: n_images')

    try:
        n_images = int(n_images_str)
    except:
        raise RuntimeError(f'Cannot convert n_images={n_images_str} to an integer. Must be an integer >= 1.')

    if n_images < 1:
        raise RuntimeError(f'Invalid n_images={n_images}. Must be an integer >= 1.')

    return n_images


def update_config(old_config, config_updates):
    new_config = OrderedDict({param: config_updates.get(param, old_config[param])
                              for param in DAQ_CONFIG_FIELDS})

    validate_config(new_config)

    return new_config


def validate_config(new_config):
    pass


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
