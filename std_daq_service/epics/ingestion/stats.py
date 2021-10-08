from time import time


class EpicsIngestionStats (object):
    def __init__(self, service_name, output_file='stats.log'):
        self.service_name = service_name
        self.output_file = output_file

        self.stats = {}
        self._reset_stats()

        self.output_file = open(self.output_file, 'a')
        self.start_time = time()

    def _reset_stats(self):
        self.stats = {
            'n_events': 0,
            'n_bytes': 0,
        }

    def record(self, pv_name, event_timestamp, connected,
               value, value_timestamp, value_status, value_type):
        self.stats['n_events'] += 1
        # TODO: Get the real size of the update.
        self.stats['n_bytes'] += 1

    def write_stats(self):
        # TODO: Prepare the correct output
        stats_output = "SOMETHNG"
        self._reset_stats()

        self.output_file.write(stats_output)

    def close(self):
        self.output_file.close()
