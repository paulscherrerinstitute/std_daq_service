import unittest
from time import sleep

from std_daq_service.broker.client import BrokerClient
from std_daq_service.broker.common import TEST_BROKER_URL, ACTION_REQUEST_SUCCESS
from std_daq_service.broker.primary_service import PrimaryBrokerService
from std_daq_service.broker.status_aggregator import StatusAggregator


class TestStatusRecorder(unittest.TestCase):
    def test_status_recorder(self):
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

        recorder = StatusAggregator(status_change_callback=on_status_change)

        recorder.on_status_message("1", request, header)
        header['action'] = 'action_2'
        recorder.on_status_message("1", request, header)

        self.assertEqual(len(last_status['services'][header['source']]), 2)

        request['another'] = 'one'
        header['source'] = 'service_2'
        recorder.on_status_message("2", request, header)

        self.assertTrue('service_1' not in last_status['services'])
        self.assertTrue('service_2' in last_status['services'])

    def test_wait_for_complete(self):

        tag = "beamline_1"

        request = {
            'this': 'request'
        }

        aggregator = StatusAggregator()
        client = BrokerClient(broker_url=TEST_BROKER_URL,
                              tag=tag,
                              status_callback=aggregator.on_status_message)

        def service_request_callback(request_id, request):
            sleep(0.01)
            pass

        service_1 = PrimaryBrokerService(TEST_BROKER_URL, "service_name", "beamline_1", service_request_callback)
        service_2 = PrimaryBrokerService(TEST_BROKER_URL, "service_name_2", request_callback=service_request_callback)
        sleep(0.1)

        request_id = client.send_request(request)
        aggregator.wait_for_complete(request_id, timeout=3)
        sleep(0.1)

        client.stop()
        service_1.stop()
        service_2.stop()

    def test_wait_for_complete_timeout(self):
        aggregator = StatusAggregator()

        with self.assertRaises(TimeoutError):
            aggregator.wait_for_complete("request_id", 0.1)

    def test_cache_max_len(self):
        def noop(request_id, status):
            pass

        recorder = StatusAggregator(noop)

        max_request_id = 200
        for i in range(max_request_id):
            recorder.on_status_message(request_id=i,
                                       header={'source': "service_1",
                                               'action': ACTION_REQUEST_SUCCESS,
                                               'message': "something"},
                                       request={})

        self.assertEqual(recorder.cache_length, len(recorder.status))

        for i in range(recorder.cache_length):
            # We expect the last 'recorder.cache_length' ids to be present in the cache.
            expected_value = max_request_id - recorder.cache_length + i
            self.assertEqual(recorder.request_id_buffer[i], expected_value)

            self.assertTrue(expected_value in recorder.status)
