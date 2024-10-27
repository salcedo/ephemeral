import logging
import random
import sys

import yaml

from providers import Providers


logging.basicConfig(level=logging.INFO)


class EphemeralVPN:
    def __init__(self, config_file):
        try:
            with open(config_file) as f:
                self.config = yaml.load(f.read())
        except:
            print('Unable to open config file: ' + config_file)
            sys.exit(1)

        self.providers = []
        for provider in self.config['providers']:
            p = Providers[provider](self.config['providers'][provider])

            if p is not None:
                self.providers.append(p)

    def list_instances(self):
        instances = []
        for provider in self.providers:
            instances += provider.list_instances()

        return instances

    def random_instance(self):
        provider = random.choice(self.providers)
        location = random.choice(provider.locations)

        old_instances = self.list_instances()
        provider.create_instance(location)
        self.destroy_instances(old_instances)

    def destroy_instances(self, instances=None):
        if instances is None:
            instances = self.list_instances()

        for instance in instances:
                instance['provider'].suicide(instance)


if __name__ == '__main__':
    e = EphemeralVPN('config.yml')

    if len(sys.argv) == 1:
        e.random_instance()
    elif len(sys.argv) > 1:
        if sys.argv[1].lower() == 'list':
            print('{0:20} {1:15} {2:25} {3:15}'.format(
                'Provider',
                'Location',
                'Instance ID',
                'Address'))

            for instance in e.list_instances():
                print('{0:20} {1:15} {2:25} {3:15}'.format(
                    instance['provider'].name,
                    instance['location'],
                    instance['instance_id'],
                    instance['address']))
        elif sys.argv[1].lower() == 'destroy':
            e.destroy_instances()
