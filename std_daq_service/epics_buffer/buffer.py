import time


class EpicsBuffer(object):
    def __init__(self, pv_names):
        self.pv_names = pv_names
        self.cache = {}

        event_timestamp = time.time()

        for pv_name in self.pv_names:
            self.cache[pv_name] = {
                'event_timestamp': event_timestamp,
                'connected': False,
                'value': None,
                'value_timestamp': None,
                'value_status': None
            }

    def change_callback(self, pv_name, event_timestamp, connected,
                        value, value_timestamp, value_status):

        self.cache[pv_name] = {
            'event_timestamp': event_timestamp,
            'connected': connected,
            'value': value,
            'value_timestamp': value_timestamp,
            'value_status': value_status
        }
