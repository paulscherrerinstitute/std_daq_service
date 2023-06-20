import logging
import struct
import time
import epics
from epics.dbr import AlarmStatus, DBE_VALUE, DBE_ALARM, DBE_LOG
import numpy as np

_logger = logging.getLogger("EpicsBufferReceiver")


def silence_ca_library_errors(_):
    pass


# Disable spamming from the library.
epics.ca.replace_printf_handler(silence_ca_library_errors)

FTYPE_STRING = 0
FTYPE_INT16 = 1
FTYPE_FLOAT32 = 2
FTYPE_ENUM = 3
FTYPE_CHAR = 4
FTYPE_INT32 = 5
FTYPE_FLOAT64 = 6

FTYPE_TIME_STRING = 14
FTYPE_TIME_INT16 = 15
FTYPE_TIME_FLOAT32 = 16
FTYPE_TIME_ENUM = 17
FTYPE_TIME_CHAR = 18
FTYPE_TIME_INT32 = 19
FTYPE_TIME_FLOAT64 = 20

# Struct mapping found https://docs.python.org/3/library/struct.html
# Format: EPICS_DBR_TYPE : (buffer dtype, struct type)
epics_dbr_type_mapping = {
    FTYPE_STRING: ("string", 's'),
    FTYPE_INT16: ("i2", "h"),
    FTYPE_FLOAT32: ("f4", "f"),
    FTYPE_ENUM: ("u2", "H"),
    FTYPE_CHAR: ("u1", 'c'),
    FTYPE_INT32: ("i4", "i"),
    FTYPE_FLOAT64: ("f8", "d"),

    FTYPE_TIME_STRING: ("string", "s"),
    FTYPE_TIME_INT16: ("i2", "h"),
    FTYPE_TIME_FLOAT32: ("f4", "f"),
    FTYPE_TIME_ENUM: ("u2", "H"),
    FTYPE_TIME_CHAR: ("u1", "c"),
    FTYPE_TIME_INT32: ("i4", "i"),
    FTYPE_TIME_FLOAT64: ("f8", "d")
}


def convert_ca_to_buffer(value, ftype):
    value_type = type(value)
    shape = (1,)

    if value_type == np.ndarray:
        shape = value.shape
        dtype = f"{value.dtype.kind}{value.dtype.itemsize}"
        value = value.tobytes()

    elif value_type == str:
        dtype = "string"
    else:
        if ftype not in epics_dbr_type_mapping:
            message = f"Ftype {ftype} missing in epics DBR mapping for value_type {value_type}."
            raise RuntimeError(message)

        dtype = epics_dbr_type_mapping[ftype][0]
        value = struct.pack(epics_dbr_type_mapping[ftype][1], value)

    shape_bytes = struct.pack(f"<{len(shape)}I", *shape)

    return value, dtype, shape_bytes


class EpicsReceiver(object):
    def __init__(self, pv_names, change_callback, use_archiver_precision=False):
        self.pvs = []
        self.change_callback = change_callback
        # Initialization to None -> first disconnect is inserted in Redis, because compared value is b'0'
        self.connected_channels = {pv_name: None for pv_name in pv_names}

        automonitor_mask = DBE_VALUE | DBE_ALARM
        if use_archiver_precision:
            _logger.info("Using archiver precision.")
            automonitor_mask |= DBE_LOG

        _logger.info("Starting PV connections.")

        for pvname in pv_names:
            _logger.debug(f"Connecting to PV {pvname}.")

            self.pvs.append(epics.PV(
                pvname=pvname,
                callback=self.value_callback,
                connection_callback=self.connection_callback,
                form='time',
                auto_monitor=automonitor_mask
            ))

            # Initialize buffer with empty event.
            self.change_callback(pvname, {
                "id": int(time.time() * (10 ** 6)),
                "type": b'',
                "shape": b'',
                "value": b'',
                "status": b'',
                "connected": 0})

        _logger.info("Processed all PV connections.")

    def value_callback(self, pvname, value, timestamp, status, ftype, **kwargs):
        value, dtype, shape = convert_ca_to_buffer(value, ftype)
        timestamp = int(timestamp * (10 ** 6))

        self.change_callback(pvname, {
            "id": timestamp,
            "type": dtype,
            "shape": shape,
            "value": value,
            "connected": 1,
            "status": AlarmStatus(status).name}
        )

    def connection_callback(self, pvname, conn, **kwargs):
        # We already registered this state.
        if self.connected_channels[pvname] == conn:
            return

        self.connected_channels[pvname] = conn
        _logger.debug(f"Channel {pvname} changed connected status to connected:{conn}.")

        # We send updates only when we transition from a connected to a disconnected state.
        if not conn:
            _logger.warning(f"Channel {pvname} disconnected.")

            self.change_callback(pvname, {
                "id": int(time.time() * (10 ** 6)),
                "type": b'',
                "shape": b'',
                "value": b'',
                "status": b'',
                "connected": 0}
            )

