import logging
import time
import epics
from epics.dbr import AlarmStatus

_logger = logging.getLogger("EpicsBufferReceiver")


def silence_ca_library_errors(_):
    pass


# Disable spamming from the library.
epics.ca.replace_printf_handler(silence_ca_library_errors)


class EpicsReceiver(object):
    def __init__(self, pv_names, change_callback):
        self.pvs = []
        self.change_callback = change_callback
        self.connected_channels = {pv_name: False for pv_name in pv_names}

        _logger.info("Starting PV connections.")

        for pvname in pv_names:
            _logger.debug(f"Connecting to PV {pvname}.")

            self.pvs.append(epics.PV(
                pvname=pvname,
                callback=self.value_callback,
                connection_callback=self.connection_callback,
                form='time',
                auto_monitor=True
            ))

        _logger.info("Processed all PV connections.")

    def value_callback(self, pvname, value, timestamp, status, type, **kwargs):
        event_timestamp = time.time_ns()

        self.change_callback(pvname, {
            "event_timestamp": event_timestamp,
            "connected": True,
            "value": value,
            "value_timestamp": timestamp,
            "value_status": AlarmStatus(status).name,
            "value_type": type[5:]}
        )

    def connection_callback(self, pvname, conn, **kwargs):
        event_timestamp = time.time_ns()

        # We already registered this state.
        if self.connected_channels[pvname] == conn:
            return

        self.connected_channels[pvname] = conn
        _logger.debug(f"Channel {pvname} changed connected status to conntected:{conn}.")

        # We send updates only when we transition from a connected to a disconnected state.
        if not conn:
            _logger.warning(f"Channel {pvname} disconnected.")

            self.change_callback(pvname, {
                "event_timestamp": event_timestamp,
                "connected": conn,
                "value": None,
                "value_timestamp": None,
                "value_status": None,
                "value_type": None}
            )

