import logging
import os
import stat
import cv2
import numpy as np
import zmq
from std_buffer.image_metadata_pb2 import ImageMetadata, ImageMetadataDtype


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
    with SwitchUser(user_id):
        path_folder = os.path.dirname(output_file)
        if not os.path.exists(path_folder):
            raise RuntimeError(f'Output file folder {path_folder} does not exist. Please create it first.')


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


class SwitchUser(object):
    def __init__(self, user_id):
        self.user_id = user_id

    def __enter__(self):
        if self.user_id > 0:
            _logger.info(f"Setting effective user_id to {self.user_id}.")
            os.seteuid(self.user_id)
        else:
            _logger.info(f"Using process user_id.")

    def __exit__(self, exc_type, exc_val, exc_tb):
        # In case you set the user_id, revert back to original.
        if self.user_id > 0:
            _logger.info(f"Returning effective user_id to {os.getuid()}.")
            os.seteuid(os.getuid())


def get_font_scale(target_height_in_pixels: int):
    # Set a base scale
    scale = 1.0
    # Use a typical text
    text = "Test text"
    # Get the size of the text box
    ((text_width, text_height), _) = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, scale, 1)
    # Calculate the target font scale
    target_font_scale = target_height_in_pixels / text_height
    return target_font_scale


def draw_module_map(image, daq_config):
    rectangle_color = (0, 255, 0)  # Green
    rectangle_thickness = 2  # Pixels
    text_color = (0, 255, 0)  # Green

    for key, (x_start, y_start, x_end, y_end) in daq_config['module_positions'].items():
        # Draw the rectangle
        cv2.rectangle(image, (x_start, y_start), (x_end, y_end), rectangle_color, rectangle_thickness)

        # Draw the text for the module and its submodules
        text_start_y = y_start if y_start < y_end else y_end
        size_y = abs(y_end - y_start) + 20
        gap_y = size_y // 5
        font_scale = get_font_scale(30)
        y_smaller = y_start if y_start < y_end else y_end
        y_bigger = y_end if y_end > y_start else y_start

        submodule_info = next((item for item in daq_config['submodule_info'] if item["submodule"] == int(key)), None)
        if submodule_info:
            cv2.putText(image, f"module_id: {key}", (x_start + rectangle_thickness + 20,
                                                     text_start_y + (1 * gap_y)),
                        cv2.FONT_HERSHEY_SIMPLEX, font_scale, text_color, rectangle_thickness)
            cv2.putText(image, f"hostname: {submodule_info['hostname']}",
                        (x_start + rectangle_thickness + 20, text_start_y + (2 * gap_y)),
                        cv2.FONT_HERSHEY_SIMPLEX, font_scale,
                        text_color, rectangle_thickness)
            cv2.putText(image, f"port: {submodule_info['port']}",
                        (x_start + rectangle_thickness + 20, text_start_y + (3 * gap_y)),
                        cv2.FONT_HERSHEY_SIMPLEX, font_scale,
                        text_color, rectangle_thickness)
            cv2.putText(image, f"row: {submodule_info['row']}, column: {submodule_info['column']}",
                        (x_start + rectangle_thickness + 20, text_start_y + (4 * gap_y)), cv2.FONT_HERSHEY_SIMPLEX,
                        font_scale,
                        text_color, rectangle_thickness)

        arrow_color = (0, 255, 0)  # Red
        arrow_thickness = 20  # Pixels
        arrow_line_length = 100  # Length of the arrow's line
        arrow_tip_length = 30  # Length of the two lines that make the arrow tip

        arrow_start_x = x_end - 35  # adjust these as needed

        if y_start > y_end:  # if true, arrow points upwards
            arrow_start_y = y_smaller + arrow_line_length + 20  # adjust these as needed
            arrow_end_y = arrow_start_y - arrow_line_length
            # Draw the arrow line
            cv2.line(image, (arrow_start_x, arrow_start_y), (arrow_start_x, arrow_end_y), arrow_color,
                     arrow_thickness)
            # Draw the arrow tip
            cv2.line(image, (arrow_start_x, arrow_end_y),
                     (arrow_start_x - arrow_tip_length // 2, arrow_end_y + arrow_tip_length), arrow_color,
                     arrow_thickness)
            cv2.line(image, (arrow_start_x, arrow_end_y),
                     (arrow_start_x + arrow_tip_length // 2, arrow_end_y + arrow_tip_length), arrow_color,
                     arrow_thickness)
        else:  # arrow points downwards
            arrow_start_y = y_bigger - 120  # adjust these as needed
            arrow_end_y = arrow_start_y + arrow_line_length
            # Draw the arrow line
            cv2.line(image, (arrow_start_x, arrow_start_y), (arrow_start_x, arrow_end_y), arrow_color,
                     arrow_thickness)
            # Draw the arrow tip
            cv2.line(image, (arrow_start_x, arrow_end_y),
                     (arrow_start_x - arrow_tip_length // 2, arrow_end_y - arrow_tip_length), arrow_color,
                     arrow_thickness)
            cv2.line(image, (arrow_start_x, arrow_end_y),
                     (arrow_start_x + arrow_tip_length // 2, arrow_end_y - arrow_tip_length), arrow_color,
                     arrow_thickness)
