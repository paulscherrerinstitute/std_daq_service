import zmq
import numpy as np
import cv2

IPC_BASE = "ipc:///tmp"

def get_stream_addresses(detector_name):

    command_address = f'{IPC_BASE}/{detector_name}-writer'
    in_status_address = f'{IPC_BASE}/{detector_name}-writer-status-sync'
    out_status_address = f'{IPC_BASE}/{detector_name}-writer-status'
    image_metadata_address = f'{IPC_BASE}/{detector_name}-image'

    return command_address, in_status_address, out_status_address, image_metadata_address


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
