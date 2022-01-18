import os
import struct
import unittest
from multiprocessing import Process
from time import sleep, time

import h5py
from epics import CAProcess
import numpy as np
from redis import Redis

from std_daq_service.epics_buffer.buffer import start_epics_buffer
from std_daq_service.epics_writer.service import download_pv_data
from std_daq_service.epics_writer.writer import EpicsH5Writer
from tests.test_epics_buffer import start_test_ioc


class TestEpicsWriter(unittest.TestCase):

    def test_basic_writer(self):
        file_name = "test.h5"
        pv_name = "test_pv"
        pv_data = None

        self.addCleanup(os.remove, file_name)

        with EpicsH5Writer(output_file=file_name) as writer:
            writer.write_pv(pv_name, pv_data)

        with h5py.File(file_name) as input_file:
            self.assertTrue(pv_name in input_file)

    def test_data_download(self):
        pv_names = ['ioc:pv_1', 'ioc:pv_2', 'ioc:pv_3']
        parameters = {
            'service_name': "test_buffer",
            'redis_host': "localhost",
            'pv_names': pv_names,
        }

        ioc_process = Process(target=start_test_ioc)
        ioc_process.start()

        recv_process = CAProcess(target=start_epics_buffer, kwargs=parameters)
        recv_process.start()

        redis = Redis()

        start_t = int(time() * 1000)
        sleep(2)
        stop_t = int(time() * 1000)

        try:
            for pvname in pv_names:
                pv_data = download_pv_data(redis, pvname, start_timestamp=start_t, stop_timestamp=stop_t)
                self.assertTrue(pv_data)

                for id, value in pv_data:
                    redis_id = int(id.decode().split("-")[0])
                    epics_id = int(float(value[b'id'].decode()) * 1000)
                    self.assertTrue(redis_id > epics_id)

                    dtype = value[b'type'].decode()
                    if dtype == 'string':
                        value_array = value[b'value'].decode()
                    else:
                        shape = struct.unpack(f"<{len(value[b'shape']) // 4}I", value[b'shape'])
                        value_array = np.frombuffer(value[b'value'], dtype=dtype).reshape(shape)

                        self.assertTrue(len(value_array) > 0)

                    connected = bool(value[b'connected'])
                    status = value[b'status'].decode()

                    self.assertTrue(connected)
                    self.assertTrue(status)
        finally:
            redis.close()

            ioc_process.terminate()
            recv_process.terminate()
