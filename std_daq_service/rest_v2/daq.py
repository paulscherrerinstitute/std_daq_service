import ansible_runner
import time

from std_daq_service.rest_v2.stats import ImageMetadataStatsDriver
from std_daq_service.rest_v2.utils import update_config

DEFAULT_DEPLOYMENT_FOLDER = '/etc/std_daq/deployment'
INVENTORY_FILE = '/inventory.yml'
SERVICE_FILE = '/inventory.yml'


class AnsibleConfigDriver(object):
    status_mapping = {
        'starting': 'Execution started',
        'successful': 'Done',
        'running': 'Running tasks',
    }

    def __init__(self, ansible_repo_folder=DEFAULT_DEPLOYMENT_FOLDER, status_callback=lambda x: None):
        self.repo_folder = ansible_repo_folder
        self.services_file = ansible_repo_folder + SERVICE_FILE
        self.inventory_file = ansible_repo_folder + INVENTORY_FILE

        self.status = {'state': None, 'status': None, 'deployment_id': None, 'deployment_start': None}
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

    def configure(self):
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

    def get_config(self):
        return {"detector_name": "Eiger9M",
                "detector_type": "eiger",
                "n_modules": 72,
                "bit_depth": 32,
                "image_pixel_height": 2016,
                "image_pixel_width": 2016,
                "start_udp_port": 2000}


class DaqRestManager(object):
    def __init__(self, daq_config, stats_driver: ImageMetadataStatsDriver, config_driver: AnsibleConfigDriver):
        self.daq_config = daq_config
        self.stats_driver = stats_driver
        self.config_driver = config_driver

    def get_config(self):
        return self.config_driver.get_config()

    def set_config(self, config_updates):
        new_config = update_config(self.get_config(), config_updates)
        self.config_driver.deploy_config(new_config)

    def get_stats(self):
        pass

    def get_logs(self, n_logs):
        pass

    def get_deployment_status(self):
        pass

    def close(self):
        pass