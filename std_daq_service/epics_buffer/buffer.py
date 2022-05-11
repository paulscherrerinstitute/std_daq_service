import logging
from time import sleep, time_ns

import epics
from redis import Redis

from std_daq_service.epics_buffer.receiver import EpicsReceiver
from std_daq_service.epics_buffer.stats import EpicsBufferStats

# Redis buffer for 1 day.
# max 10/second updates for regular channels.
PV_MAX_LEN = 3600 * 24 * 10
# 100/second updates for pulse_id channel.
PULSE_ID_MAX_LEN = 3600 * 24 * 100
# Name of the stream for pulse_id mapping.
PULSE_ID_NAME = "pulse_id"
PULSE_ID_NAME_REVERSE = "pulse_id_reverse"
# Interval for printing out statistics.
STATS_INTERVAL = 10

_logger = logging.getLogger("EpicsBuffer")


def start_epics_buffer(service_name, redis_host, pv_names,
                       pulse_id_pv=None, redis_port=6379, use_archiver_precision=False):
    _logger.debug(f'Connecting to PVs: {pv_names}')

    redis = Redis(host=redis_host, port=redis_port)
    stats = EpicsBufferStats(service_name=service_name)

    def on_pv_change(pv_name, value):
        redis.xadd(pv_name, value, maxlen=PV_MAX_LEN)
        stats.record(pv_name, value)

    EpicsReceiver(pv_names=pv_names, change_callback=on_pv_change, use_archiver_precision=use_archiver_precision)

    if pulse_id_pv:
        _logger.info(f"Adding pulse_id_pv {pulse_id_pv} to buffer.")

        def on_pulse_id_change(value, timestamp, **kwargs):
            if not value:
                _logger.warning("Pulse_id PV empty.")
                return

            pulse_id = int(value)

            epics_timestamp = int(timestamp * (10 ** 6))
            buffer_timestamp = time_ns()

            try:
                redis.xadd(PULSE_ID_NAME, {"buffer_timestamp": buffer_timestamp,
                                           'epics_timestamp': epics_timestamp},
                           id=pulse_id, maxlen=PULSE_ID_MAX_LEN)

                redis.xadd(PULSE_ID_NAME_REVERSE, {"pulse_id": pulse_id,
                                                   'epics_timestamp': epics_timestamp},
                           maxlen=PULSE_ID_MAX_LEN)
            except Exception as e:
                _logger.warning(f"Cannot insert pulse_id {pulse_id} to Redis. {str(e)}")

        epics.PV(pvname=pulse_id_pv,
                 callback=on_pulse_id_change,
                 form='time',
                 auto_monitor=True)

    try:
        while True:
            sleep(STATS_INTERVAL)
            stats.write_stats()

    except KeyboardInterrupt:
        _logger.info("Received interrupt signal. Exiting.")

    except Exception:
        _logger.exception("Epics buffer error.")

    finally:
        stats.close()
