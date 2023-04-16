from threading import Thread, Event
from time import time

from zmq import Again

from std_buffer.std_daq.image_metadata_pb2 import ImageMetadata

import zmq

# For how long to accumulate statistics in seconds.
STATS_INTERVAL = 1


class ImageMetadataStatsDriver(object):
    def __init__(self, ctx, image_stream_url):
        self.image_stream_url = image_stream_url
        self.ctx = ctx

        self._stop_event = Event()
        self.stats = {"bytes_per_second": 0, "images_per_second": 0}
        self._stats_thread = Thread(target=self._collect_stats)
        self._stats_thread.start()

    def _collect_stats(self):
        receiver = self.ctx.socket(zmq.SUB)
        receiver.connect(self.image_stream_url)
        receiver.setsockopt(zmq.SUBSCRIBE, b'')

        image_meta = ImageMetadata()
        n_bytes_interval = 0
        n_images_interval = 0

        start_time = time()
        while self._stop_event.is_set():
            try:
                meta_raw = receiver.recv()
                image_meta.ParseFromString(meta_raw)
            except Again:
                continue

            diff = time() - start_time
            if diff > STATS_INTERVAL:
                self.stats = {"bytes_per_second": n_bytes_interval/STATS_INTERVAL,
                              "images_per_second": n_images_interval/STATS_INTERVAL}

                start_time = start_time + STATS_INTERVAL
                n_bytes_interval = 0
                n_images_interval = 0

            # TODO: Extract the real bit_depth.
            n_bytes_interval += image_meta.height * image_meta.width * 2
            n_images_interval += 1

    def get_stats(self):
        return self.stats

    def close(self):
        self._stop_event.set()
        self._stats_thread.join()
