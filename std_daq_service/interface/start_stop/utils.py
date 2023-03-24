import zmq
import numpy as np
import cv2


def get_stream_addresses(detector_name):

    image_metadata_stream = f'{detector_name}-image'
    writer_control_stream = f'{detector_name}-writer'
    writer_status_stream = f'{detector_name}-writer-status'

    return image_metadata_stream, writer_control_stream, writer_status_stream


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
