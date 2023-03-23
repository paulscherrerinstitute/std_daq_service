import ansible_runner
import time

class AnsibleInterface(object):
    status_mapping = {
        'starting': 'Execution started',
        'successful': 'Done',
        'running': 'Running tasks',
    }

    def __init__(self, ansible_repo_folder='/etc/std_daq/deployment', status_callback=lambda x:None):
        self.repo_folder = ansible_repo_folder
        self.services_file = ansible_repo_folder + '/services.yml'
        self.inventory_file = ansible_repo_folder + '/inventory.yml'

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


def status_callback(status):
    print(status)


ansible_interface = AnsibleInterface('/home/babic_a/git/staging.gf/', status_callback)
print(ansible_interface.deploy())
