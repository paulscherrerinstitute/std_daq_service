import random
import unittest

from pcaspy import Driver, SimpleServer
from std_daq_service.epics_buffer.receiver import EpicsReceiver


class TestEpicsReceiver(unittest.TestCase):
    def test_events(self):
        pv_names = ["ioc:pv_1", "ioc:pv_2"]

        buffer = []

        def callback_function(**kwargs):
            buffer.append(kwargs)

        EpicsReceiver(pv_names, callback_function)

        class TestIoc(Driver):
            prefix = "ioc:"
            pvdb = {
                "pv_1": {"scan": 1},
                "pv_2": {"scan": 2}
            }

            def __init__(self):
                Driver.__init__(self)

            def read(self, reason):
                value = random.random()
                return value

        ioc_server = SimpleServer()
        ioc_server.createPV(TestIoc.prefix, TestIoc.pvdb)
        driver = TestIoc()

        while len(buffer) < 5:
            ioc_server.process(0.1)

        # First 2 records come as connection updates.
        self.assertEqual({buffer[0]['pv_name'], buffer[1]['pv_name']}, set(pv_names))
        self.assertEqual(buffer[0]["value"], None)
        self.assertEqual(buffer[1]["value"], None)

        # We should get at least 1 value update from each PV.
        pv_updates = set()
        for i in range(2, 5):
            pv_updates.add(buffer[i]["pv_name"])
            self.assertTrue(buffer[i]['value'] is not None)
        self.assertEqual(pv_updates, set(pv_names))
