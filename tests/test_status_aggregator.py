import unittest
from threading import Thread
from time import sleep

from sf_daq_service.common import broker_config
from sf_daq_service.common.broker_client import BrokerClient
from sf_daq_service.common.broker_worker import BrokerWorker
from sf_daq_service.watcher.status_aggregator import StatusAggregator


class TestStatusAggregator(unittest.TestCase):
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

        aggregator = StatusAggregator(on_status_change_function=on_status_change)

        aggregator.on_broker_message("1", header, request)
        header['action'] = 'action_2'
        aggregator.on_broker_message("1", header, request)

        self.assertEqual(len(last_status['services'][header['source']]), 2)

        request['another'] = 'one'
        header['source'] = 'service_2'
        aggregator.on_broker_message("2", header, request)

        self.assertTrue('service_1' not in last_status['services'])
        self.assertTrue('service_2' in last_status['services'])

    def test_BrokerClient_with_status_aggregator(self):
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
        status_changes = []

        aggregator = StatusAggregator(on_status_change_function=status_change)
        client = BrokerClient(broker_url=broker_config.TEST_BROKER_URL,
                              status_tag=status_tag,
                              on_status_message_function=aggregator.on_broker_message)
        t_client = Thread(target=client.start)
        t_client.start()

        worker = BrokerWorker(broker_url=broker_config.TEST_BROKER_URL,
                              request_tag=service_tag,
                              name=service_name,
                              on_request_message_function=lambda x, y: "result")
        t_worker = Thread(target=worker.start)
        t_worker.start()

        sleep(0.1)
        client.send_request(request_tag, request)
        sleep(0.1)

        self.assertEqual(len(status_changes), 2)

        worker.stop()
        t_worker.join()
        sleep(0.1)
        client.stop()
        t_client.join()

