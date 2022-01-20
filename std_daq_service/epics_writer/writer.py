import logging
import numpy as np
import os
import struct
from collections import Counter

import h5py

_logger = logging.getLogger("EpicsWriterFile")


def prepare_data_for_writing(pv_name, pv_data):
    if not pv_data:
        _logger.warning(f"PV data for {pv_name} is empty.")
        return

    n_data_points = len(pv_data)

    dtypes_count = Counter(value[b'type'] for _, value in pv_data)
    if len(dtypes_count) > 1:
        _logger.warning(f'Multiple data types for {pv_name}: {dtypes_count}')
        return
    dtype = dtypes_count.most_common(1)[0][0].decode()
    dataset_type = dtype
    if dataset_type == 'string':
        dataset_type = object

    shape_count = Counter(value[b'shape'] for _, value in pv_data)
    if len(shape_count) > 1:
        _logger.warning(f'Multiple data shapes for {pv_name}: {dtypes_count}')
        return
    shape_bytes = shape_count.most_common(1)[0][0]
    dshape = struct.unpack(f"<{len(shape_bytes) // 4}I", shape_bytes)
    dataset_shape = [n_data_points] + list(dshape)

    dataset_value = np.zeros(shape=dataset_shape, dtype=dataset_type)
    dataset_timestamp = np.zeros(shape=[n_data_points, 1], dtype='<f8')
    dataset_status = np.zeros(shape=[n_data_points, 1], dtype=object)
    dataset_connected = np.zeros(shape=[n_data_points, 1], dtype='<u1')

    for index, data_point in enumerate(pv_data):
        redis_id, value = data_point

        timestamp = float(value[b'id'].decode())
        dataset_timestamp[index] = timestamp

        if dtype == 'string':
            data_point_value = value[b'value'].decode()
        else:
            data_point_value = np.frombuffer(value[b'value'], dtype=dtype).reshape(dshape)
        dataset_value[index] = data_point_value

        connected = int(value[b'connected'])
        dataset_connected[index] = connected

        status = value[b'status'].decode()
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

        # TODO: Implement metadata writing
        _logger.warning(f"Received metadata but function not implemented. {metadata}")

    def write_pv(self, pv_name, pv_data):

        n_data_points, dtype, dataset_timestamp, dataset_value, dataset_connected, dataset_status = \
            prepare_data_for_writing(pv_name, pv_data)

        self.file.create_dataset(f'{pv_name}/timestamp', data=dataset_timestamp)
        self.file.create_dataset(f'{pv_name}/value', data=dataset_value)
        self.file.create_dataset(f'{pv_name}/connected', data=dataset_connected)
        self.file.create_dataset(f'{pv_name}/status', data=dataset_status)
