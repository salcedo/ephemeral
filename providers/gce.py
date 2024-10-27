import random

from libcloud.compute.types import Provider
from libcloud.compute.providers import get_driver

from providers.provisioner import fabric_provisioner


class EphemeralProviderGoogleCompute:
    name = 'Google Compute Engine'

    def __init__(self, config):
        self.service_account_email = config['service_account_email']
        self.pem_file = config['pem_file']
        self.project_id = config['project_id']
        self.type = config['type']
        self.locations = config['locations']

        driver = get_driver(Provider.GCE)
        self.gce = driver(
            self.service_account_email,
            self.pem_file,
            project=self.project_id)

    def list_instances(self):
        instances = []
        for node in self.gce.list_nodes(ex_zone='all'):
            if node.extra['status'] != 'RUNNING' or \
                    node.extra['name'] != 'ephemeralvpn':
                continue

            instances.append({
                'provider': self,
                'instance_id': node.extra['id'],
                'location': node.extra['zone'].name,
                'address': node.public_ips[0]
            })

        return instances

    def create_instance(self, location):
        userdata = coreos_ignition()

        self.gce.create_node(
            name='ephemeralvpn',
            size=self.type,
            image='coreos-stable',
            location=self.random_zone(location),
            ex_metadata={'user-data': userdata})

        print('[+GCE] Created instance in ' + location)

    def suicide(self, instance=None):
        for node in self.gce.list_nodes(ex_zone='all'):
            if node.extra['status'] == 'RUNNING' and \
                    node.extra['name'] == 'ephemeralvpn':
                node.destroy()
                print('[-GCE] Destroyed instance.')

    def random_zone(self, location):
        zones = []
        for loc in self.gce.list_locations():
            if loc.name.startswith(location):
                zones.append(loc.name)

        return random.choice(zones)
