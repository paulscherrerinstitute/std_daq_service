import json
from logging import getLogger

from redis import Redis

from std_daq_service.epics_writer.writer import EpicsH5Writer

_logger = getLogger("EpicsWriterService")

# Max 10 seconds pulse_id mismatch.
MAX_PULSE_ID_MISMATCH = 1000


def extract_request(request):
    try:
        start_pulse_id = request["start_pulse_id"]
        stop_pulse_id = request['stop_pulse_id']

        pv_list = request['channels']
        output_file = request['output_file']
        metadata = request.get('metadata', None)
    except KeyError as e:
        raise Exception('Invalid request from broker. Missing required fields.') from e

    _logger.info(f"Write request from {start_pulse_id} to {stop_pulse_id} into {output_file}.")
    _logger.debug(f"Metadata: {metadata}")
    _logger.debug(f"Requested channels: {pv_list}")

    return start_pulse_id, stop_pulse_id, pv_list, output_file, metadata


def map_pulse_id_to_timestamp_range(redis, start_pulse_id, stop_pulse_id):
    _logger.debug(f"Mapping from {start_pulse_id} to {stop_pulse_id}.")

    def read_timestamp(response, original_pulse_id):
        if not response:
            raise RuntimeError(f"Cannot map {original_pulse_id} to timestamp.")

        # Response in format [(b'pulse_id-0', {b'timestamp': b'1639480220636463612'})]
        received_pulse_id = int(response[0][0].decode().split('-')[0])
        timestamp = int(response[0][1]["timestamp".encode()].decode())

        if abs(original_pulse_id - received_pulse_id) > MAX_PULSE_ID_MISMATCH:
            raise RuntimeError(f"Received pulse_id {received_pulse_id} "
                               f"too far away from requested pulse_id {original_pulse_id}.")

        return timestamp

    start_timestamp = read_timestamp(response=redis.xrevrange("pulse_id", max=start_pulse_id, count=1),
                                     original_pulse_id=start_pulse_id)
    stop_timestamp = read_timestamp(response=redis.xrange("pulse_id", min=stop_pulse_id, count=1),
                                    original_pulse_id=stop_pulse_id)

    _logger.debug("Mapped to range from {start_timestamp} to {stop_timestamp}.")

    return start_timestamp, stop_timestamp


def download_pv_data(redis, pv, start_timestamp, stop_timestamp):
    _logger.debug(f'Downloading PV {pv} data from {start_timestamp} to {stop_timestamp}.')
    data = []

    # First data point: either exactly on the timestamp or first from the past.
    data.extend(redis.xrevrange(pv, max=start_timestamp, count=1))
    # Range in between the first data point and the last data point (exclusive).
    data.extend(redis.xrange(pv, min=f'({start_timestamp}', max=f'({stop_timestamp}-0'))
    # Last data point: either exactly on the timestamp of next in the future.
    data.extend(redis.xrange(pv, min=stop_timestamp, count=1))

    _logger.debug(f"Downloaded {len(data)} data points for PV {pv}.")

    # Response in format [(b'event_timestamp-0', {b'json': b'JSON_STRING'})]
    return data


class EpicsWriterService(object):
    def __init__(self, redis_host, redis_port=6379):
        self.redis_host = redis_host
        self.redis_port = redis_port

        self._cancel_request = None
        self._current_request = None

    def on_request(self, request_id, request):
        # We take into account only kill requests that come after the start of the current request.
        self._cancel_request = None
        self._current_request = request_id

        start_pulse_id, stop_pulse_id, pv_list, output_file, metadata = extract_request(request)

        redis = Redis(host=self.redis_host, port=self.redis_port)
        try:
            start_timestamp, stop_timestamp = map_pulse_id_to_timestamp_range(redis, start_pulse_id, stop_pulse_id)

            with EpicsH5Writer(output_file=output_file) as writer:
                writer.write_metadata(metadata)

                for pv_name in pv_list:
                    try:
                        pv_data = download_pv_data(redis, pv_name, start_timestamp, stop_timestamp)
                        writer.write_pv(pv_name, pv_data)
                    except Exception as e:
                        _logger.exception(f"Error while writing PV {pv_name}.")
                        raise

                    if self._cancel_request == self._current_request:
                        raise Exception("User requested interruption.")
        finally:
            redis.close()

    def on_kill(self, request_id):
        self._cancel_request = request_id
