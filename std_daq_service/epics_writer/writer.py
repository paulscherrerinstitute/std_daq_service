import logging
import os
import h5py

_logger = logging.getLogger("EpicsWriterFile")


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

        if not pv_data:
            _logger.warning(f"PV data for {pv_name} is empty.")
            return

        # All the data points have the same fields - defined in the epics buffer.
        fields = pv_data[0].keys()

        for field in fields:
            self.file.create_dataset(f'{pv_name}/{field}', data=[x[field] for x in pv_data])
