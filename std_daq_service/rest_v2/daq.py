import logging
import os
from collections import OrderedDict

import h5py

from std_daq_service.rest_v2.utils import update_config, SwitchUser

_logger = logging.getLogger("DaqRestManager")
# milliseconds
RECV_TIMEOUT = 100


class DaqRestManager(object):
    def __init__(self, storage):
        self.storage = storage

    def get_config(self):
        return self.storage.get_config()

    def set_config(self, config_updates):
        config_id, daq_config = self.storage.get_config()
        new_daq_config = update_config(daq_config, config_updates)

        _logger.info(f"Set new daq_config {new_daq_config}")
        self.storage.set_config(new_daq_config)
        return new_daq_config

    def get_stats(self):
        return self.storage.get_stat()

    def get_logs(self, n_logs):
        logs = self.storage.get_logs(n_logs)
        for log_id, log_data in logs.items():
            reports = self.storage.get_reports(log_id)
            log_data['reports'] = reports

        return logs

    def get_deployment_status(self):
        return self.storage.get_deployment_status()

    def get_image_data(self, log_id, i_image, user_id):
        log = self.storage.get_log(log_id)
        filename = log['info']['output_file']

        with SwitchUser(user_id):
            file = h5py.File(filename)
            dataset_name = list(file)[0]
            dataset = file[dataset_name + '/data']
            data = dataset[i_image]
            return data

    def get_file_metadata(self, log_id, user_id):
        log = self.storage.get_log(log_id)
        filename = log['info']['output_file']

        with SwitchUser(user_id):
            file_stats = os.stat(filename)

            file = h5py.File(filename)
            dataset_name = list(file)[0]
            dataset = file[dataset_name + '/data']

            return OrderedDict({
                'filename': filename,
                'file_size': file_stats.st_size,
                'log_id': log_id,
                'dataset_name': dataset_name,
                'n_images': dataset.shape[0],
                'image_pixel_height': dataset.shape[1],
                'image_pixel_width': dataset.shape[2],
                'dtype': str(dataset.dtype)
            })
