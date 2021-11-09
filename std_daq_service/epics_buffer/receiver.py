import logging
import time
import epics
from epics.dbr import AlarmStatus

_logger = logging.getLogger("EpicsBuffer")


def silence_ca_library_errors(_):
    pass


epics.ca.replace_printf_handler(silence_ca_library_errors)


class EpicsReceiver(object):
    def __init__(self, pv_names, change_callback):
        self.pv_names = pv_names
        self.pvs = []
        self.change_callback = change_callback

        for pvname in self.pv_names:
            self._init_buffer(pvname)

            _logger.debug(f"Connecting to PV {pvname}.")

            self.pvs.append(epics.PV(
                pvname=pvname,
                callback=self.value_callback,
                connection_callback=self.connection_callback,
                form='time',
                auto_monitor=True
            ))

    def _init_buffer(self, pvname):
        event_timestamp = time.time()
        _logger.debug(f"Initializing PV {pvname}.")

        self.change_callback(pvname, {
            "event_timestamp": event_timestamp,
            "connected": None,
            "value": None,
            "value_timestamp": None,
            "value_status": None,
            "value_type": None
        })

    def value_callback(self, pvname, value, timestamp, status, type, **kwargs):
        event_timestamp = time.time()

        self.change_callback(pvname, {
            "event_timestamp": event_timestamp,
            "connected": True,
            "value": value,
            "value_timestamp": timestamp,
            "value_status": AlarmStatus(status).name,
            "value_type": type[5:]}
        )

    def connection_callback(self, pvname, conn, **kwargs):
        event_timestamp = time.time()

        self.change_callback(pvname, {
            "event_timestamp": event_timestamp,
            "connected": conn,
            "value": None,
            "value_timestamp": None,
            "value_status": None,
            "value_type": None}
        )
