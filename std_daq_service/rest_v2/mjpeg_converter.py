import argparse
import logging
from time import sleep

import zmq
import json
from flask import Flask, Response
import cv2
import numpy as np
from flask_cors import CORS
from zmq import Again

from std_daq_service.rest_v2.utils import validate_config

app = Flask(__name__)
CORS(app)

WIDTH = 800
HEIGHT = 600
# milliseconds
RECV_TIMEOUT = 500

_logger = logging.getLogger('MJPEG Stream')
LIVE_STREAM_URL = 'tcp://localhost:20000'

@app.route('/')
def index():
    return "Welcome to the MJPG Stream Demo!"


@app.route('/live')
def live_stream():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')


def generate_frames():

    context = zmq.Context()
    receiver = context.socket(zmq.SUB)
    receiver.connect(LIVE_STREAM_URL)
    receiver.setsockopt_string(zmq.SUBSCRIBE, "")
    receiver.setsockopt(zmq.RCVTIMEO, RECV_TIMEOUT)

    full_circle = True

    while True:
        try:
            raw_meta, raw_data = receiver.recv_multipart()
            meta = json.loads(raw_meta.decode('utf-8'))
            new_frame = np.frombuffer(raw_data, dtype=meta['type']).reshape(meta['shape'])

            # Flip the image vertically.
            new_frame = cv2.flip(new_frame, 0)

            # Scale image to 8 bits with full range.
            min_val = new_frame.min()
            max_val = new_frame.max() or 1

            frame = ((new_frame - min_val) * (255.0 / (max_val - min_val))).clip(0, 255).astype(np.uint8)
            image_id = meta["frame"]

        except Again:
            frame = np.zeros(shape=(HEIGHT, WIDTH), dtype=np.uint8)
            image_id = None
        
        image = cv2.resize(frame, (WIDTH, HEIGHT))
        # apply a color scheme to the grayscale image
        image = cv2.applyColorMap(image, cv2.COLORMAP_HOT)

        font = cv2.FONT_HERSHEY_SIMPLEX
        # Valid image.
        if image_id is not None:
            text = 'Frame {}'.format(image_id)
            text_color = (0, 255, 0)
        else:
            text = 'No data'
            text_color = (0, 0, 255)
            # Display circle next to text to show connection to the mjpeg stream.
            image = cv2.circle(image,  (160, HEIGHT - 40), 8, (0, 0, 255), -1 if full_circle else 2)
            full_circle = not full_circle

        text_size = cv2.getTextSize(text, font, 1, 2)[0]
        cv2.putText(image, text, (10, HEIGHT - text_size[1] - 10), font, 1, text_color, 2)

        # encode the color image as JPEG
        _, buffer = cv2.imencode('.jpg', image)
        image_bytes = buffer.tobytes()

        # yield the frame for the MJPG stream
        yield b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + image_bytes + b'\r\n'

    receiver.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='MJPEG converter')
    parser.add_argument("live_stream_address", type=str, help="Path to JSON config file.")
    parser.add_argument("--rest_port", type=int, help="Port for REST api", default=5001)

    args = parser.parse_args()
    rest_port = args.rest_port
    LIVE_STREAM_URL = args.live_stream_address

    logging.basicConfig(level=logging.INFO)
    _logger.info(f"Starting MJPEG streamer on {rest_port} for live stream {LIVE_STREAM_URL}.")

    app.run(host='0.0.0.0', port=rest_port, threaded=True)
