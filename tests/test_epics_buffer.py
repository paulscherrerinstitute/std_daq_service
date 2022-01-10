import json
import os
import random
import unittest
from multiprocessing import Process
from time import sleep
import numpy as np

from epics import CAProcess
from pcaspy import Driver, SimpleServer
from redis import Redis

from std_daq_service.epics_buffer.buffer import RedisJsonSerializer, start_epics_buffer, PULSE_ID_NAME
from std_daq_service.epics_buffer.receiver import EpicsReceiver
from std_daq_service.epics_buffer.stats import EpicsBufferStats


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

    def test_receiver(self):
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

            print(buffer)

            self.assertEqual({x['name'] for x in buffer}, set(pv_names))

            # First record from each PV is an empty one.
            for i in range(len(pv_names)):
                self.assertEqual(buffer[i]['data']["status"], "UDF")

            # We should get at least 1 value update from each PV.
            pv_updates = set()
            for i in range(len(pv_names), len(buffer)):
                pv_updates.add(buffer[i]["name"])
                self.assertTrue(buffer[i]['data'] is not None)
            self.assertEqual(pv_updates, set(pv_names))

        finally:
            ioc_process.terminate()

    def test_buffer(self):
        pulse_id_pv = 'ioc:pulse_id'
        pv_names = ['ioc:pv_1', 'ioc:pv_2', 'ioc:pv_3']

        parameters = {
            'service_name': "test_buffer",
            'redis_host': "localhost",
            'pv_names': pv_names,
            'pulse_id_pv': pulse_id_pv
        }

        ioc_process = Process(target=start_test_ioc)
        ioc_process.start()

        recv_process = CAProcess(target=start_epics_buffer, kwargs=parameters)
        recv_process.start()

        try:

            redis = Redis(decode_responses=True)
            # Remove old keys so test is always the same.
            redis.delete(*(pv_names + [PULSE_ID_NAME]))

            sleep(2)
            data = redis.xread({name: 0 for name in pv_names}, count=100, block=1000)

            received_channels = set()
            for channel in data:
                pv_name = channel[0]
                channel_data = channel[1]

                received_channels.add(pv_name)

                for data_point in channel_data:
                    point_timestamp = data_point[0]
                    point_value = data_point[1]['json']

                    json_data = json.loads(point_value)
                    self.assertTrue(json_data["event_timestamp"] > 0)

        finally:
            recv_process.terminate()
            ioc_process.terminate()

    def test_stats(self):
        n_bytes = 1000
        n_events = 100
        n_channels_changed = 10
        log_output = "temp.log"

        if os.path.exists(log_output):
            os.remove(log_output)

        buffer = EpicsBufferStats("test_service", log_output)
        for i in range(n_events):
            buffer.record(f"pv_{i % n_channels_changed}", np.zeros(shape=[n_bytes], dtype="uint8").tobytes())
            if i % 20 == 0:
                buffer.write_stats()

        buffer.close()

        self.assertTrue(os.path.exists(log_output))

        with open(log_output, 'r') as input_file:
            stats_output = input_file.readlines()

        os.remove(log_output)
        self.assertEqual(len(stats_output), 5)

        # Check if service identifying info is in the output.
        for line in stats_output:
            self.assertTrue("test_service" in line)
            self.assertTrue("epics_buffer" in line)


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
