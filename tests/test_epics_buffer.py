import json
import os
import random
import struct
import unittest
from multiprocessing import Process
from time import sleep
import numpy as np

from epics import CAProcess
from pcaspy import Driver, SimpleServer

from std_daq_service.epics_buffer.buffer import RedisJsonSerializer
from std_daq_service.epics_buffer.receiver import EpicsReceiver


class TestEpicsBuffer(unittest.TestCase):

    def test_redis_json_serializer(self):
        test_json = {
            "pv_1": 1,
            "pv_2": 2.2,
            "pv_3": np.zeros(shape=[10]),
            "pv_4": "test",
            "pv_5": None,
            "pv_6": ""
        }

        raw_data = json.dumps(test_json, cls=RedisJsonSerializer).encode("utf-8")
        converted_data = json.loads(raw_data.decode("utf-8"))

        for name, value in test_json.items():
            if name != "pv_3":
                self.assertEqual(value, converted_data.get(name))
            else:
                self.assertEqual(value.tolist(), converted_data.get(name))

    def test_events(self):
        pv_names = ["ioc:pv_1", "ioc:pv_2", 'ioc:pv_3']
        buffer = []

        def callback_function(pv_name, change):
            buffer.append({'name': pv_name, 'data': change})

        ioc_process = Process(target=start_test_ioc)
        ioc_process.start()

        try:

            EpicsReceiver(pv_names, callback_function)

            while len(buffer) < 10:
                sleep(0.1)

            # First 2 records come as connection updates.
            self.assertEqual({x['name'] for x in buffer}, set(pv_names))
            self.assertEqual(buffer[0]['data']["value"], None)
            self.assertEqual(buffer[1]['data']["value"], None)

            # We should get at least 1 value update from each PV.
            pv_updates = set()
            for i in range(2, 5):
                pv_updates.add(buffer[i]["name"])
                self.assertTrue(buffer[i]['data'] is not None)
            self.assertEqual(pv_updates, set(pv_names))

        finally:
            ioc_process.terminate()

    def test_receiver(self):
        sampling_pv = 'ioc:pulse_id'
        pv_names = ['ioc:pv_1', 'ioc:pv_2']

        expected_file_name = BUFFER_FILENAME_FORMAT % 0
        if os.path.exists(expected_file_name):
            os.remove(expected_file_name)

        ioc_process = Process(target=start_test_ioc)
        ioc_process.start()

        recv_process = CAProcess(target=start_epics_buffer, args=(sampling_pv, pv_names, '.'))
        recv_process.start()

        while True:
            try:
                file_size = os.stat(expected_file_name).st_size
                # 315 is the buffer data size for our test cases.
                if file_size > (315 * 20) + TOTAL_INDEX_BYTES:
                    break
            except:
                pass

        recv_process.terminate()
        ioc_process.terminate()

        with open(expected_file_name, 'rb') as buffer_file:
            buffer_file.seek(0)
            index_data = buffer_file.read(TOTAL_INDEX_BYTES)

            for i in range(20):
                index_offset = SLOT_INDEX_BYTES * i
                pulse_id, offset, length = struct.unpack("<QQQ", index_data[index_offset:index_offset+SLOT_INDEX_BYTES])

                self.assertEqual(pulse_id, i)
                # 315 is the buffer data size for our test cases.
                self.assertTrue(length >= 315)

                buffer_file.seek(offset)
                data = json.loads(buffer_file.read(length))

                for pv_name in pv_names:
                    self.assertTrue(pv_name in data)

        os.remove(expected_file_name)


def start_test_ioc():
    class TestIoc(Driver):
        prefix = "ioc:"
        pvdb = {
            "pulse_id": {"scan": 0.1},
            "pv_1": {"scan": 1},
            "pv_2": {"scan": 2, 'type': 'string'},
            "pv_3": {"scan": 1, 'count': 10}
        }

        def __init__(self):
            Driver.__init__(self)
            self.pulse_id = 0

        def read(self, reason):
            if reason == "pulse_id":
                self.pulse_id += 1
                return self.pulse_id

            elif reason == "pv_1":
                return random.random()

            elif reason == "pv_2":
                return "String test"

            elif reason == "pv_3":
                return [random.random() for _ in range(10)]

            return None

    ioc_server = SimpleServer()
    ioc_server.createPV(TestIoc.prefix, TestIoc.pvdb)
    TestIoc()

    while True:
        ioc_server.process(0.1)
