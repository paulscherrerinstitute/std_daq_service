import logging
import signal

from redis import Redis

from std_daq_service.epics_buffer.receiver import EpicsReceiver

# Redis buffer for 1 day.
# max 10/second updates for regular channels.
REDIS_MAX_STREAM_LEN = 3600*24*10
# 100/second updates for pulse_id channel.
REDIS_PULSE_ID_MAX_STREAM_LEN = 3600*24*100

_logger = logging.getLogger("EpicsBuffer")


def start_epics_buffer(redis_host, pv_names, pulse_id_pv=None):
    _logger.debug(f'Connecting to PVs: {pv_names}')

    redis = Redis(host=redis_host)

    def on_pv_change(pv_name, value):
        redis.xadd(pv_name, value, maxlen=REDIS_MAX_STREAM_LEN)
    EpicsReceiver(pv_names=pv_names, change_callback=on_pv_change)

    if pulse_id_pv:
        _logger.info(f"Adding pulse_id_pv {pulse_id_pv} to buffer.")

        def on_pulse_id_change(_, value):
            redis.xadd("pulse_id", value, maxlen=REDIS_PULSE_ID_MAX_STREAM_LEN)
        EpicsReceiver(pv_names=[pulse_id_pv], change_callback=on_pulse_id_change)

    try:
        signal.pause()
    except KeyboardInterrupt:
        _logger.info("Received interrupt signal. Exiting.")

    except Exception:
        _logger.error("Epics buffer error.")
