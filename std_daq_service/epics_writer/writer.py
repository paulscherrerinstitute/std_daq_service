import logging
import numpy as np
import os
import struct
from collections import Counter

import h5py

_logger = logging.getLogger("EpicsWriterFile")


def prepare_data_for_writing(pv_name, pv_data):
    n_data_points = len(pv_data)

    def get_prevalent_value(field: bytes):
        field_count = Counter(value[field] for _, value in pv_data)
        # This is the disconnected data_point.
        del field_count[b'']

        if len(field_count) == 0:
            _logger.warning(f'No valid data points for {pv_name}.')
            return

        elif len(field_count) > 1:
            _logger.warning(f'Multiple values in {pv_name} for {field}: {field_count}')
            return

        return field_count.most_common(1)[0][0]

    dtype_bytes = get_prevalent_value(b'type')
    # There is no valid data point from which to construct the datasets.
    if dtype_bytes is None:
        return
    dtype = dtype_bytes.decode()
    dataset_type = dtype
    if dataset_type == 'string':
        dataset_type = object

    shape_bytes = get_prevalent_value(b'shape')
    dshape = struct.unpack(f"<{len(shape_bytes) // 4}I", shape_bytes)
    dataset_shape = [n_data_points] + list(dshape)

    dataset_value = np.zeros(shape=dataset_shape, dtype=dataset_type)
    dataset_timestamp = np.zeros(shape=[n_data_points, 1], dtype='<u8')
    dataset_status = np.zeros(shape=[n_data_points, 1], dtype=object)
    dataset_connected = np.zeros(shape=[n_data_points, 1], dtype='<u1')

    for index, data_point in enumerate(pv_data):
        redis_id, value = data_point

        timestamp = int(value[b'id'].decode())
        dataset_timestamp[index] = timestamp

        connected = int(value[b'connected'])
        dataset_connected[index] = connected

        # If not connected, there is nothing to be set -> the value is invalid.
        if connected == 0:
            continue

        if dtype == 'string':
            data_point_value = value[b'value'].decode()
        else:
            data_point_value = np.frombuffer(value[b'value'], dtype=dataset_type).reshape(dshape)
        dataset_value[index] = data_point_value

        status = value[b'status'].decode()
        print(status)
        if status == [0]:
            raise ValueError('sa')
        dataset_status[index] = status

    return n_data_points, dtype, dataset_timestamp, dataset_value, dataset_connected, dataset_status


class EpicsH5Writer(object):
    def __init__(self, output_file):
        self.output_file = output_file
        self.datasets = {}

        path_to_file = os.path.dirname(self.output_file)
        if path_to_file:
            os.makedirs(path_to_file, exist_ok=True)

        self.file = h5py.File(self.output_file, 'w')

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def close(self):
        self.file.close()

    def write_metadata(self, metadata):

        if not metadata:
            return

        for dataset_name, value in metadata.items():
            if not isinstance(value, str):
                _logger.warning(f"Cannot set dataset {dataset_name}. Only string values supported. Value: {value}")

            self.file.create_dataset(dataset_name, dtype=h5py.special_dtype(vlen=str), data=value)

    def write_pv(self, pv_name, pv_data):

        if not pv_data:
            _logger.warning(f"PV data for {pv_name} is empty.")
            return

        self.file.create_group(pv_name)

        unpacked_data = prepare_data_for_writing(pv_name, pv_data)
        if unpacked_data:
            n_data_points, dtype, dataset_timestamp, dataset_value, dataset_connected, dataset_status = unpacked_data

            h5_dataset_type = dtype if dtype != "string" else h5py.special_dtype(vlen=str)
            self.file.create_dataset(f'{pv_name}/value', data=dataset_value, dtype=h5_dataset_type)

            self.file.create_dataset(f'{pv_name}/timestamp', data=dataset_timestamp)
            self.file.create_dataset(f'{pv_name}/connected', data=dataset_connected)
            self.file.create_dataset(f'{pv_name}/status', data=dataset_status, dtype=h5py.special_dtype(vlen=str))
