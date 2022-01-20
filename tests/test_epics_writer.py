import os
import unittest
from multiprocessing import Process
from time import sleep, time

import h5py
from epics import CAProcess
from redis import Redis

from std_daq_service.epics_buffer.buffer import start_epics_buffer
from std_daq_service.epics_writer.service import download_pv_data
from std_daq_service.epics_writer.writer import EpicsH5Writer, prepare_data_for_writing
from tests.test_epics_buffer import start_test_ioc


class TestEpicsWriter(unittest.TestCase):

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
            for pv_name in pv_names:
                pv_data = download_pv_data(redis, pv_name, start_timestamp=start_t, stop_timestamp=stop_t)
                self.assertTrue(pv_data)

                n_data_points, dtype, dataset_timestamp, dataset_value, dataset_connected, dataset_status = \
                    prepare_data_for_writing(pv_name, pv_data)

                self.assertTrue(n_data_points > 0)
                self.assertEqual(dataset_timestamp.shape, (n_data_points, 1))
                self.assertEqual(dataset_connected.shape, (n_data_points, 1))
                self.assertEqual(dataset_status.shape, (n_data_points, 1))

                self.assertEqual(dataset_status.shape[0], n_data_points)

        finally:
            redis.close()

            ioc_process.terminate()
            recv_process.terminate()

    def test_basic_writer(self):
        file_name = "test.h5"
        self.addCleanup(os.remove, file_name)

        pv_names = ['ioc:pv_1', 'ioc:pv_2', 'ioc:pv_3', "missing"]
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
            with EpicsH5Writer(output_file=file_name) as writer:
                for pv_name in pv_names:
                    pv_data = download_pv_data(redis, pv_name, start_timestamp=start_t, stop_timestamp=stop_t)
                    writer.write_pv(pv_name, pv_data)
        finally:
            redis.close()

            ioc_process.terminate()
            recv_process.terminate()

        with h5py.File(file_name, 'r') as input_file:
            if pv_name != "missing":
                self.assertTrue(pv_name in input_file)
