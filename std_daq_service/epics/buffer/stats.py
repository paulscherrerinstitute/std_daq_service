import logging
from time import time_ns

_logger = logging.getLogger("EpicsBufferStats")

DEFAULT_OUTPUT_FILE = '/var/log/std-daq/perf.log'


class EpicsBufferStats (object):
    def __init__(self, service_name, output_file=None):
        self.service_name = service_name

        if output_file is None:
            output_file = DEFAULT_OUTPUT_FILE
        self.output_file = output_file
        _logger.info(f"Starting service {service_name} stats logging to {self.output_file}.")

        self.stats = {}
        self._reset_stats()

        self.output_file = open(self.output_file, 'a', buffering=1)
        self.start_time = time_ns()

    def _reset_stats(self):
        self.stats = {
            'n_events': 0,
            'n_bytes': 0,
            'channel_changed': set()
        }

    def record(self, name, data):
        self.stats['n_events'] += 1
        self.stats['n_bytes'] += len(data)
        self.stats['channel_changed'].add(name)

    def write_stats(self):
        end_time = time_ns()
        throughput = self.stats['n_bytes'] / (end_time - self.start_time) * 10**9
        n_channels_changed = len(self.stats["channel_changed"])

        # InfluxDB line protocol
        stats_output = f'epics_buffer,service_name={self.service_name}' \
                       f' n_events={self.stats["n_events"]}i' \
                       f' n_bytes={self.stats["n_bytes"]}i' \
                       f' n_channels_changed={n_channels_changed}i' \
                       f' throughput_bytes={throughput}' \
                       f' {end_time}\n'

        self.start_time = end_time
        self._reset_stats()

        self.output_file.write(stats_output)

    def close(self):
        self.output_file.close()
