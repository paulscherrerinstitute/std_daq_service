from copy import deepcopy
from threading import Thread, Event
from time import time

from zmq import Again

from std_buffer.std_daq.image_metadata_pb2 import ImageMetadata

import zmq
import copy

from std_daq_service.rest_v2.redis_storage import StdDaqRedisStorage
from std_daq_service.rest_v2.utils import dtype_to_bytes

# For how long to accumulate statistics in seconds.
STATS_INTERVAL = 1
# Receive timeout in milliseconds
RECV_TIMEOUT = 1000

EMPTY_STATS = {
    'detector': {"bytes_per_second": 0, "images_per_second": 0},
    'writer': {'bytes_per_second': 0, "writes_per_second": 0}
}


class StatsDriver(object):
    def __init__(self, ctx, storage: StdDaqRedisStorage, image_stream_url, writer_status_url):
        self.ctx = ctx
        self.storage = storage
        self.image_stream_url = image_stream_url
        self.writer_status_url = writer_status_url

        self._stop_event = Event()
        self.stats = copy.deepcopy(EMPTY_STATS)
        self._stats_thread = Thread(target=self._collect_stats)
        self._stats_thread.start()

    def _collect_stats(self):
        detector_receiver = self.ctx.socket(zmq.SUB)
        detector_receiver.connect(self.image_stream_url)
        detector_receiver.setsockopt(zmq.SUBSCRIBE, b'')
        detector_receiver.setsockopt(zmq.RCVTIMEO, RECV_TIMEOUT)

        writer_receiver = self.ctx.socket(zmq.SUB)
        writer_receiver.connect(self.writer_status_url)
        writer_receiver.setsockopt(zmq.SUBSCRIBE, b'')
        writer_receiver.setsockopt(zmq.RCVTIMEO, RECV_TIMEOUT)

        image_meta = ImageMetadata()
        n_bytes_detector = 0
        n_images_detector = 0
        n_bytes_writer = 0
        n_images_writer = 0

        last_n_write_completed = 0
        image_n_bytes = None

        start_time = time()
        while not self._stop_event.is_set():
            new_bytes_detector = 0
            new_images_detector = 0
            new_bytes_writer = 0
            new_images_writer = 0

            poller = zmq.Poller()
            poller.register(detector_receiver, zmq.POLLIN)
            poller.register(writer_receiver, zmq.POLLIN)

            try:
                socks = dict(poller.poll(RECV_TIMEOUT))

                if detector_receiver in socks:
                    meta_raw = detector_receiver.recv(flags=zmq.NOBLOCK)
                    image_meta.ParseFromString(meta_raw)
                    image_n_bytes = image_meta.width * image_meta.height * \
                                    (dtype_to_bytes[ImageMetadata.Dtype.Name(image_meta.dtype)])

                    new_bytes_detector = image_n_bytes
                    new_images_detector = 1

                if writer_receiver in socks and image_n_bytes:
                    writer_status = writer_receiver.recv_json(flags=zmq.NOBLOCK)
                    self.storage.add_writer_status(writer_status)

                    n_written = writer_status['acquisition']['stats']['n_write_completed']

                    # Start of a new write
                    if n_written == 0:
                        last_n_write_completed = 0

                    new_images_writer = n_written - last_n_write_completed
                    last_n_write_completed = n_written

                    new_bytes_writer = image_n_bytes
            except Again:
                self.stats = copy.deepcopy(EMPTY_STATS)
                continue

            diff = time() - start_time
            if diff > STATS_INTERVAL:
                self.stats = {
                    'detector': {
                        "bytes_per_second": n_bytes_detector/STATS_INTERVAL,
                        "images_per_second": n_images_detector/STATS_INTERVAL},
                    'writer': {
                        "bytes_per_second": n_bytes_writer / STATS_INTERVAL,
                        "images_per_second": n_images_writer / STATS_INTERVAL}
                }

                start_time = start_time + STATS_INTERVAL
                n_bytes_detector = 0
                n_images_detector = 0
                n_bytes_writer = 0
                n_images_writer = 0

            n_bytes_detector += new_bytes_detector
            n_images_detector += new_images_detector

            n_bytes_writer += new_bytes_writer
            n_images_writer += new_images_writer

    def get_stats(self):
        return self.stats

    def close(self):
        self._stop_event.set()
        self._stats_thread.join()
