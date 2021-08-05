import logging
import time
import epics
from epics.dbr import AlarmStatus

_logger = logging.getLogger("EpicsReceiver")


def silence_ca_library_errors(_):
    pass


epics.ca.replace_printf_handler(silence_ca_library_errors)


class EpicsReceiver(object):
    def __init__(self, pv_names, change_callback):
        self.pv_names = pv_names
        self.pvs = []
        self.change_callback = change_callback

        for pv_name in self.pv_names:
            _logger.debug(f"Adding PV {pv_name}.")

            self.pvs.append(epics.PV(
                pvname=pv_name,
                callback=self.value_callback,
                connection_callback=self.connection_callback,
                form='time',
                auto_monitor=True
            ))

    def value_callback(self, pvname, value, timestamp, status, **kwargs):

        event_timestamp = time.time()

        self.change_callback(
            pv_name=pvname,
            event_timestamp=event_timestamp,
            connected=True,
            value=value,
            value_timestamp=timestamp,
            value_status=AlarmStatus(status).name
        )

    def connection_callback(self, pvname, conn, **kwargs):

        event_timestamp = time.time()

        self.change_callback(
            pv_name=pvname,
            event_timestamp=event_timestamp,
            connected=True,
            value=None,
            value_timestamp=None,
            value_status=None
        )
