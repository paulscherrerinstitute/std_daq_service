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

app = Flask(__name__)
CORS(app)

STREAM_WIDTH = 800
STREAM_HEIGHT = 600
# milliseconds
RECV_TIMEOUT = 500
LIVE_STREAM_URL = 'tcp://localhost:20000'

_logger = logging.getLogger('MJpegLiveStream')


class MJpegLiveStream(object):
    def __init__(self, ctx, live_stream_url):
        self.ctx = ctx
        self.live_stream_url = live_stream_url

    def generate_frames(self):
        receiver = self.ctx.socket(zmq.SUB)
        receiver.connect(self.live_stream_url)
        receiver.setsockopt_string(zmq.SUBSCRIBE, "")
        receiver.setsockopt(zmq.RCVTIMEO, RECV_TIMEOUT)

        full_circle = True
        meta = None

        _logger.info("Live stream started.")
        n_timeouts = 0
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

                n_timeouts = 0

            except Again:
                if n_timeouts < 3:
                    n_timeouts += 1
                    continue

                frame = np.zeros(shape=(STREAM_HEIGHT, STREAM_WIDTH), dtype=np.uint8)
                image_id = None

            image = cv2.resize(frame, (STREAM_WIDTH, STREAM_HEIGHT))
            # apply a color scheme to the grayscale image
            image = cv2.applyColorMap(image, cv2.COLORMAP_HOT)

            font = cv2.FONT_HERSHEY_SIMPLEX
            # Valid image.
            if image_id is not None:
                text = 'Frame {}'.format(image_id)
                text_color = (0, 255, 0)

                shape, dtype = meta['shape'], meta['type']
                metadata_text = f'{shape} ({dtype})'
                metadata_text_size = cv2.getTextSize(metadata_text, font, 1, 2)[0]
                cv2.putText(image, metadata_text, (10, metadata_text_size[1] + 20),
                            font, 1, text_color, 2)

            else:
                text = 'No data'
                text_color = (0, 0, 255)
                # Display circle next to text to show connection to the mjpeg stream.
                image = cv2.circle(image, (160, STREAM_HEIGHT - 40), 8, (0, 0, 255), -1 if full_circle else 2)
                full_circle = not full_circle

            text_size = cv2.getTextSize(text, font, 1, 2)[0]
            cv2.putText(image, text, (10, STREAM_HEIGHT - text_size[1] - 10), font, 1, text_color, 2)

            # encode the color image as JPEG
            _, buffer = cv2.imencode('.jpg', image)
            image_bytes = buffer.tobytes()

            # yield the frame for the MJPG stream
            yield b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + image_bytes + b'\r\n'


@app.route('/')
def live_stream():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')


def generate_frames():
    context = zmq.Context()
    stream = MJpegLiveStream(context, LIVE_STREAM_URL)

    return stream.generate_frames()


def main():
    parser = argparse.ArgumentParser(description='MJPEG converter')
    parser.add_argument("live_stream_address", type=str, help="Address of std-daq live stream.")
    parser.add_argument("--rest_port", type=int, help="Port for serving the stream", default=5001)

    args = parser.parse_args()
    rest_port = args.rest_port

    global LIVE_STREAM_URL
    LIVE_STREAM_URL = args.live_stream_address

    logging.basicConfig(level=logging.INFO)
    _logger.info(f"Starting MJPEG streamer on {rest_port} for live stream {LIVE_STREAM_URL}.")

    app.run(host='0.0.0.0', port=rest_port, threaded=True)


if __name__ == '__main__':
    main()
