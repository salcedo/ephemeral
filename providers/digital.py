import digitalocean

from providers.provisioner import fabric_provisioner


class EphemeralProviderDigitalOcean:
    name = 'Digital Ocean'

    def __init__(self, config):
        self.token = config['token']
        self.type = config['type']
        self.locations = config['locations']

        self.manager = digitalocean.Manager(token=self.token)

    def list_instances(self):
        instances = []
        for droplet in self.manager.get_all_droplets():
            if droplet.status != 'active' or droplet.name != 'ephemeralvpn':
                continue

            instances.append({
                'provider': self,
                'instance_id': droplet.id,
                'location': droplet.region['slug'],
                'address': droplet.ip_address})

        return instances

    def create_instance(self, location):
        userdata = coreos_ignition()

        droplet = digitalocean.Droplet(
            token=self.token,
            name='ephemeralvpn',
            region=location,
            image='coreos-stable',
            size_slug=self.type,
            ssh_keys=self.manager.get_all_sshkeys(),
            user_data=userdata)

        droplet.create()

        print('[+DO] Created droplet in ' + location)

    def suicide(self, instance):
        droplet = self.manager.get_droplet(instance['instance_id'])
        droplet.destroy()

        print('[-DO] Destroyed droplet in ' + instance['location'])
