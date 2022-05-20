from logging import getLogger
from redis import Redis

from std_daq_service.epics_buffer.buffer import PULSE_ID_NAME_REVERSE
from std_daq_service.epics_writer.writer import EpicsH5Writer

_logger = getLogger("EpicsWriterService")

# Max 10 seconds pulse_id mismatch.
MAX_PULSE_ID_MISMATCH = 1000
TIMELINE_TIMESTAMP_PAD = 5
EMPTY_PULSE_ID_MAPPING = 0


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

        if abs(original_pulse_id - received_pulse_id) > MAX_PULSE_ID_MISMATCH:
            raise RuntimeError(f"Received pulse_id {received_pulse_id} "
                               f"too far away from requested pulse_id {original_pulse_id}.")

        timestamp_ns = int(response[0][1]["buffer_timestamp".encode()].decode())
        timestamp = timestamp_ns // (10 ** 6)

        _logger.debug(f"Converted timestamp in nano {timestamp_ns} into milli {timestamp} format.")

        return timestamp

    start_timestamp = read_timestamp(response=redis.xrevrange("pulse_id", max=start_pulse_id, count=1),
                                     original_pulse_id=start_pulse_id)
    stop_timestamp = read_timestamp(response=redis.xrange("pulse_id", min=stop_pulse_id, count=1),
                                    original_pulse_id=stop_pulse_id)

    _logger.debug(f"Mapped to range from {start_timestamp} to {stop_timestamp}.")

    return start_timestamp, stop_timestamp


def get_pulse_id_timeline(redis: Redis, first_timestamp, last_timestamp):

    start_timestamp_id = max(first_timestamp-TIMELINE_TIMESTAMP_PAD, 0)
    stop_timestamp_id = last_timestamp + TIMELINE_TIMESTAMP_PAD

    _logger.debug(f"Creating timestamp timeline from {start_timestamp_id} to {stop_timestamp_id} "
                  f"({TIMELINE_TIMESTAMP_PAD} timestamp padding).")

    # We pad the exact pulse_id range because the timestamp might be misaligned.
    pulse_ids = redis.xrange(PULSE_ID_NAME_REVERSE, min=start_timestamp_id, max=stop_timestamp_id)

    timeline = []

    for pulse_id_record in pulse_ids:
        # Response in format [(b'buffer_timestamp-0', {b'pulse_id': b'1651066190677740000',
        #                                      b'epics_timestamp': b'1651066190674197'}), ...]

        pulse_id = int(pulse_id_record[1][b"pulse_id"].decode())
        epics_timestamp_ns = int(pulse_id_record[1][b"epics_timestamp"].decode())

        timeline.append((epics_timestamp_ns, pulse_id))

    _logger.debug(f"Generated timeline with n_elements={len(timeline)}")

    return timeline


def download_pv_data(redis: Redis, pv, start_timestamp, stop_timestamp):
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


def map_pv_data_to_pulse_id(pv_data, timeline):
    i_data = 0
    i_timeline = 0
    while i_timeline < len(timeline) and i_data < len(pv_data):
        t_timestamp = timeline[i_timeline][0]

        data_point = pv_data[i_data]
        redis_id, value = data_point
        d_timestamp = int(value[b'id'].decode())

        if d_timestamp < t_timestamp:
            value[b'pulse_id'] = EMPTY_PULSE_ID_MAPPING
            i_data += 1
            continue

        if i_timeline + 1 < len(timeline) and timeline[i_timeline+1][0] < d_timestamp:
            i_timeline += 1
            continue

        value[b'pulse_id'] = timeline[i_timeline][1]
        i_data += 1


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
            pulse_id_timeline = get_pulse_id_timeline(redis, start_timestamp, stop_timestamp)

            with EpicsH5Writer(output_file=output_file) as writer:
                writer.write_metadata(metadata)

                for pv_name in pv_list:
                    try:
                        pv_data = download_pv_data(redis, pv_name, start_timestamp, stop_timestamp)
                        if pv_data:
                            map_pv_data_to_pulse_id(pv_data, pulse_id_timeline)

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
