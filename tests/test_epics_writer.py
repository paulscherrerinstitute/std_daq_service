import os
import unittest
from multiprocessing import Process
from time import sleep, time

import h5py
from epics import CAProcess
from redis import Redis

from std_daq_service.epics.buffer import start_epics_buffer, PULSE_ID_NAME
from std_daq_service.epics.writer.service import download_pv_data, map_pv_data_to_pulse_id, EpicsWriterService
from std_daq_service.epics.writer import EpicsH5Writer, prepare_data_for_writing
from tests.test_epics_buffer import start_test_ioc


class TestEpicsWriter(unittest.TestCase):

    def test_data_download(self):
        pv_names = ['ioc:pv_1', 'ioc:pv_2', 'ioc:pv_3', 'ioc:pulse_id']
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

        pv_names = ['ioc:pv_1', 'ioc:pv_2', 'ioc:pv_3', "not_connected"]
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

        metadata = {
            'general/user': '17502',
            'general/process': 'sf_daq_broker.broker_manager',
            'general/created': '2022-02-04 18:55:39.374424',
            'general/instrument': 'alvra'
        }

        try:
            with EpicsH5Writer(output_file=file_name) as writer:
                for pv_name in pv_names:
                    pv_data = download_pv_data(redis, pv_name, start_timestamp=start_t, stop_timestamp=stop_t)

                    writer.write_pv(pv_name, pv_data)

                writer.write_metadata(metadata)
        finally:
            redis.close()

            ioc_process.terminate()
            recv_process.terminate()

        with h5py.File(file_name, 'r') as input_file:
            self.assertTrue(pv_name in input_file)

            if pv_name not in ("not_connected", "missing"):
                self.assertTrue(f'{pv_name}/value' in input_file)
            elif pv_name == 'not_connected':
                self.assertTrue(pv_name in input_file)
            elif pv_name == "missing":
                self.assertTrue(pv_name not in input_file)

            for key, value in metadata.items():
                self.assertTrue(key in input_file)
                self.assertEqual(input_file[key][()].decode(), metadata[key])

    def test_service(self):
        file_name = "test.h5"
        self.addCleanup(os.remove, file_name)

        pv_names = ['ioc:pv_1', 'ioc:pv_2', 'ioc:pv_3', "not_connected"]
        parameters = {
            'service_name': "test_buffer",
            'redis_host': "localhost",
            'pv_names': pv_names,
            'pulse_id_pv': 'ioc:' + PULSE_ID_NAME
        }

        redis = Redis()
        # Remove old keys so test is always the same.
        redis.delete(*pv_names)
        redis.delete(PULSE_ID_NAME)

        ioc_process = Process(target=start_test_ioc)
        ioc_process.start()

        recv_process = CAProcess(target=start_epics_buffer, kwargs=parameters)
        recv_process.start()

        redis_host = '127.0.0.1'
        service = EpicsWriterService(redis_host=redis_host)

        request = {
            "start_pulse_id": 10,
            'stop_pulse_id': 20,
            'channels': pv_names,
            'output_file': file_name,
            'metadata': {
                "name": 'roberto'
            }
        }

        sleep(3)

        try:
            service.on_request(123, request)

            with h5py.File(file_name) as input_file:
                for pv in pv_names:
                    if pv != 'not_connected':
                        self.assertTrue('pulse_id' in input_file[pv])
        finally:
            ioc_process.terminate()
            recv_process.terminate()

    def test_pulse_id_mapping(self):
        # [(redis_id, {b'id': timestamp})]
        pv_data = [(0, {b'id': b'1'}),
                   (0, {b'id': b'4'}),
                   (0, {b'id': b'7'}),
                   (0, {b'id': b'8'}),
                   (0, {b'id': b'10'}),
                   (0, {b'id': b'11'}),
                   (0, {b'id': b'33'})]

        # [(epics_timestamp_ns, pulse_id)]
        timeline = [(5, 5000),
                    (10, 10000),
                    (15, 15000),
                    (20, 20000),
                    (25, 25000),
                    (30, 30000)]

        expected_pulse_ids = [0, 0, 5000, 5000, 5000, 10000, 30000]

        map_pv_data_to_pulse_id(pv_data, timeline)
        pulse_ids = [x[1][b'pulse_id'] for x in pv_data]
        self.assertEqual(pulse_ids, expected_pulse_ids)
