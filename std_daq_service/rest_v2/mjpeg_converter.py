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

WIDTH = 800
HEIGHT = 600
RECV_TIMEOUT = 500 # milliseconds


@app.route('/')
def index():
    return "Welcome to the MJPG Stream Demo!"


@app.route('/live')
def live_stream():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')


def generate_frames():

    context = zmq.Context()
    receiver = context.socket(zmq.SUB)
    receiver.connect("tcp://192.168.10.228:20000")
    receiver.setsockopt_string(zmq.SUBSCRIBE, "")
    receiver.setsockopt(zmq.RCVTIMEO, RECV_TIMEOUT)

    while True:
        try:
            raw_meta, raw_data = receiver.recv_multipart()
            meta = json.loads(raw_meta.decode('utf-8'))
            frame = np.frombuffer(raw_data, dtype=meta['type']).reshape(meta['shape'])

            a = (255 - 0) / (65535 - 0)
            b = 255 - a * 65535
            frame = (a * frame + b).astype(np.uint8)
            frame = cv2.resize(frame, (WIDTH, HEIGHT))

            image_id = meta["frame"]
        except Again:
            frame = np.random.randint(0, 256, (HEIGHT, WIDTH), dtype=np.uint8)
            image_id = "No data"

        # apply a color scheme to the grayscale image
        color_frame = cv2.applyColorMap(frame, cv2.COLORMAP_JET)

        font = cv2.FONT_HERSHEY_SIMPLEX
        text = 'Frame {}'.format(image_id)
        text_size = cv2.getTextSize(text, font, 1, 2)[0]
        cv2.putText(color_frame, text, (10, HEIGHT - text_size[1] - 10), font, 1, (0, 255, 0), 2)

        # encode the color image as JPEG
        _, buffer = cv2.imencode('.jpg', color_frame)
        frame = buffer.tobytes()

        # yield the frame for the MJPG stream
        yield b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + frame + b'\r\n'

    receiver.close()


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
