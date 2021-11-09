import os
import h5py


class EpicsH5Writer(object):
    def __init__(self, output_file, n_pulses):
        self.output_file = output_file
        self.n_pulses = n_pulses
        self.is_init = False
        self.datasets = {}

        path_to_file = os.path.dirname(self.output_file)
        os.makedirs(path_to_file, exist_ok=True)

        self.file = h5py.File(self.output_file, 'w')

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def init_datasets(self, data):

        def create_pv_dataset(pv_name, suffix, dtype, shape):
            dataset_name = pv_name + "/" + suffix
            self.datasets[dataset_name] = self.file.create_dataset(
                dataset_name, shape=shape, dtype=dtype)

        for name, data in data.items():
            data_dtype = ""
            data_shape = (1,)
            meta_shape = (self.n_pulses,)

            create_pv_dataset(name, "data", data_dtype, data_shape)
            create_pv_dataset(name, "alarm", h5py.special_dtype(vlen=str), meta_shape)
            create_pv_dataset(name, "connection", "bool", meta_shape)
            create_pv_dataset(name, "timestamp", "int64", meta_shape)
            create_pv_dataset(name, "pulse_id", "uint64", meta_shape)

    def write(self, index, pulse_id, data):
        if not self.is_init:
            self.init_datasets(data)

        for pv_name, data in data.items():
            self.file[pv_name + "/data"][index] = data["data"]["value"]
            self.file[pv_name + "/alarm"][index] = data["data"]["alarm"]
            self.file[pv_name + "/connection"][index] = data["connection"]["status"]
            self.file[pv_name + "/timestamp"][index] = data["data"]["timestamp"]
            self.file[pv_name + "/pulse_id"][index] = pulse_id

    def close(self):
        self.file.close()
