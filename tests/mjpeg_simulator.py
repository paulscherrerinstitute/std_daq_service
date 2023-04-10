from time import sleep

from flask import Flask, Response
import cv2
import numpy as np
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

WIDTH = 800
HEIGHT = 600


@app.route('/')
def index():
    return "Welcome to the MJPG Stream Demo!"


@app.route('/live')
def live_stream():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')


def generate_frames():
    frame_num = 0
    while True:
        # generate a random grayscale image of size 800x600
        frame = np.random.randint(0, 256, (HEIGHT, WIDTH), dtype=np.uint8)

        # apply a color scheme to the grayscale image
        color_frame = cv2.applyColorMap(frame, cv2.COLORMAP_JET)

        frame_num += 1
        font = cv2.FONT_HERSHEY_SIMPLEX
        text = 'Frame {}'.format(frame_num)
        text_size = cv2.getTextSize(text, font, 1, 2)[0]
        cv2.putText(color_frame, text, (10, HEIGHT - text_size[1] - 10), font, 1, (0, 255, 0), 2)

        # encode the color image as JPEG
        _, buffer = cv2.imencode('.jpg', color_frame)
        frame = buffer.tobytes()

        # yield the frame for the MJPG stream
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

        sleep(0.15)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
