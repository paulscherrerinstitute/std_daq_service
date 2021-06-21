import unittest
from threading import Thread
from time import sleep

from std_daq_service.common import broker_config
from std_daq_service.broker_client import BrokerClient
from std_daq_service.common.broker_worker import BrokerWorker
from std_daq_service.logger.start import print_to_console
from std_daq_service.logger.status_recorder import StatusRecorder


class TestStatusRecorder(unittest.TestCase):
    def test_status_aggregator(self):
        header = {
            'source': 'service_1',
            'action': 'action_1',
            'message': None
        }

        request = {
            'try': 'this'
        }

        def on_status_change(request_id, status):
            nonlocal last_status
            self.assertEqual(status['request'], request)
            self.assertTrue(header['source'] in status['services'])
            last_status = status

        last_status = None

        recorder = StatusRecorder(on_status_change_function=on_status_change)

        recorder.on_broker_message("1", header, request)
        header['action'] = 'action_2'
        recorder.on_broker_message("1", header, request)

        self.assertEqual(len(last_status['services'][header['source']]), 2)

        request['another'] = 'one'
        header['source'] = 'service_2'
        recorder.on_broker_message("2", header, request)

        self.assertTrue('service_1' not in last_status['services'])
        self.assertTrue('service_2' in last_status['services'])

    def test_BrokerClient_with_status_aggregator(self):
        # TODO: Fix the resources leak here.

        service_name = "noop_worker"
        service_tag = "psi.facility.beamline.#"
        request_tag = "psi.facility.beamline.profile"
        status_tag = "psi.facility.beamline.#"

        request = {
            'this': 'request'
        }

        def status_change(request_id, status):
            nonlocal status_changes
            status_changes.append((request_id, status))

            print_to_console(request_id, status)

        status_changes = []

        recorder = StatusRecorder(on_status_change_function=status_change)
        client = BrokerClient(broker_url=broker_config.TEST_BROKER_URL,
                              status_tag=status_tag,
                              on_status_message_function=recorder.on_broker_message)
        t_client = Thread(target=client.start)
        t_client.start()

        worker_1 = BrokerWorker(broker_url=broker_config.TEST_BROKER_URL,
                                request_tag=service_tag,
                                name=service_name + '_1',
                                on_request_message_function=lambda x, y: "result")
        t_worker_1 = Thread(target=worker_1.start)
        t_worker_1.start()

        worker_2 = BrokerWorker(broker_url=broker_config.TEST_BROKER_URL,
                                request_tag=service_tag,
                                name=service_name + '_2',
                                on_request_message_function=lambda x, y: "result")
        t_worker_2 = Thread(target=worker_2.start)
        t_worker_2.start()

        sleep(0.1)
        client.send_request(request_tag, request)
        sleep(0.1)

        self.assertEqual(len(status_changes), 4)

        worker_1.stop()
        t_worker_1.join()
        worker_2.stop()
        t_worker_2.join()
        sleep(0.1)
        client.stop()
        t_client.join()

    def test_cache_max_len(self):
        def noop(request_id, status):
            pass

        recorder = StatusRecorder(noop)

        max_request_id = 200
        for i in range(max_request_id):
            recorder.on_broker_message(request_id=i,
                                       header={'source': "service_1",
                                               'action': broker_config.ACTION_REQUEST_SUCCESS,
                                               'message': "something"},
                                       request={})

        self.assertEqual(recorder.cache_length, len(recorder.status))

        for i in range(recorder.cache_length):
            # We expect the last 'recorder.cache_length' ids to be present in the cache.
            expected_value = max_request_id - recorder.cache_length + i
            self.assertEqual(recorder.request_id_buffer[i], expected_value)

            self.assertTrue(expected_value in recorder.status)
