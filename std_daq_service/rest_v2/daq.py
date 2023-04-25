import json
import os

import ansible_runner
import time

from std_daq_service.rest_v2.stats import ImageMetadataStatsDriver
from std_daq_service.rest_v2.utils import update_config
from std_daq_service.writer_driver.start_stop_driver import WriterDriver

DEFAULT_DEPLOYMENT_FOLDER = '/etc/std_daq/deployment'
INVENTORY_FILE = '/inventory.yaml'
SERVICE_FILE = '/services.yaml'


class AnsibleConfigDriver(object):
    status_mapping = {
        'starting': 'Execution started',
        'successful': 'Done',
        'running': 'Running tasks',
    }

    def __init__(self, detector_name, ansible_repo_folder=DEFAULT_DEPLOYMENT_FOLDER, status_callback=lambda x: None):
        self.repo_folder = ansible_repo_folder
        if not os.path.exists(self.repo_folder):
            raise ValueError(f"Ansible repo folder {self.repo_folder} does not exist.")

        self.services_file = ansible_repo_folder + SERVICE_FILE
        if not os.path.isfile(self.services_file):
            raise ValueError(f'DAQ service file {self.services_file} does not exist.')

        self.inventory_file = ansible_repo_folder + INVENTORY_FILE
        if not os.path.isfile(self.inventory_file):
            raise ValueError(f'DAQ inventory file {self.inventory_file} does not exist.')

        self.config_file = f'{ansible_repo_folder}/configs/{detector_name}.json'
        if not os.path.isfile(self.config_file):
            raise ValueError(f'DAQ config file {self.config_file} does not exist.')

        self.status = {'state': 'READY', 'status': 'SUCCESS', 'deployment_id': None,
                       'stats': {'start_time': 0, 'end_time': 0}}
        self.status_callback = status_callback

    def _status_handler(self, data, runner_config):
        self.status['state'] = data['status']

        # Record start time and id.
        if data['status'] == 'starting':
            self.status['deployment_start'] = time.time()
            self.status['deployment_id'] = data['runner_ident']

        # Set the status for displaying.
        if data['status'] == 'failed':
            # TODO: Extract the exception from somewhere.
            self.status['status'] = 'OMG ERROR WHAT TO DOOOOO'
        else:
            self.status['status'] = self.status_mapping.get(self.status['state'], "")

        self.status_callback(self.status)

    def _event_handler(self, data):
        # Non relevant event.
        if data['event'] != 'runner_on_start':
            return

        # Task name and host in status.
        self.status['status'] = f"{data['event_data'].get('task')} on {data['event_data'].get('host')}"

        self.status_callback(self.status)

    def get_servers_facts(self):
        result = ansible_runner.run(
            private_data_dir=self.repo_folder,
            inventory=self.inventory_file, module='setup',
            quiet=True, status_handler=self._status_handler
        )

        if self.status['state'] != 'successful':
            return self.status, None

        return self.status, result

    def get_config(self):
        with open(self.config_file, 'r') as input_file:
            daq_config = json.load(input_file)

        return daq_config

    def set_config(self, daq_config):
        with open(self.config_file, 'w') as output_file:
            json.dump(daq_config, output_file)

        ansible_runner.run(
            private_data_dir=self.repo_folder,
            inventory=self.inventory_file, playbook=self.services_file, tags='config',
            quiet=True, status_handler=self._status_handler, event_handler=self._event_handler
        )

        return self.status

    def deploy(self):
        result = ansible_runner.run(
            private_data_dir=self.repo_folder,
            inventory=self.inventory_file, playbook=self.services_file, tags='all',
            quiet=True, status_handler=self._status_handler, event_handler=self._event_handler
        )

        return self.status


class DaqRestManager(object):
    def __init__(self, stats_driver: ImageMetadataStatsDriver, config_driver: AnsibleConfigDriver,
                 writer_driver: WriterDriver):
        self.stats_driver = stats_driver
        self.config_driver = config_driver
        self.deployment_status = config_driver.status
        self.writer_driver = writer_driver

    def _set_status(self, deployment_status):
        self.deployment_status = deployment_status

    def get_config(self):
        return self.config_driver.get_config()

    def set_config(self, config_updates):
        new_daq_config = update_config(self.get_config(), config_updates)
        self.config_driver.set_config(new_daq_config)

    def get_stats(self):
        return self.stats_driver.get_stats()

    def get_logs(self, n_logs):
        return self.writer_driver.get_logs(n_logs)

    def get_deployment_status(self):
        return self.deployment_status

    def close(self):
        self.stats_driver.close()
