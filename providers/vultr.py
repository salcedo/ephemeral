import logging
import time
import uuid

import requests

from providers.provisioner import fabric_provisioner


class VultrException(Exception):
    pass


class VultrAPI:
    def __init__(self, api_key):
        self.log = logging.getLogger('Vultr')
        self.api_key = api_key

    def server_list(self, tag=None, label=None):
        data = []

        if tag:
            data.append('tag=' + tag)

        if label:
            data.append('label=' + label)

        resource = 'server/list'

        if len(data) > 0:
            resource += '?' + '&'.join(data)

        servers_dict = self.request(resource)
        servers = []

        for server in servers_dict:
            servers.append(servers_dict[server])

        return servers

    def name_to_dcid(self, name):
        data = self.request('regions/list')
        dcid = ''
        for point in data:
            if name.lower() == data[point]['name'].lower():
                dcid = data[point]['DCID']
                break

        return dcid

    def cheapest_vpsplanid(self, dcid):
        planids = self.request('regions/availability_vc2?DCID=' + dcid)
        plans = self.request('plans/list_vc2')

        price_per_month = 10.0
        planid = ''

        for plan in plans:
            if int(plan) in planids:
                if float(plans[plan]['price_per_month']) < price_per_month:
                    price_per_month = float(plans[plan]['price_per_month'])
                    planid = plan

        return planid

    def request(self, resource, data=None):
        status_codes = {
            200: 'Function successfully executed.',
            400: 'Invalid API location.',
            403: 'Invalid or missing API key',
            405: 'Invalid HTTP method.',
            412: 'Request failed.',
            500: 'Internal server error.',
            503: 'Rate limit hit.'
        }

        headers = {'API-Key': self.api_key}

        url = 'https://api.vultr.com/v1/' + resource

        retries = 3
        while retries > 1:
            if retries < 3:
                time.sleep(0.5)

            if data:
                response = requests.post(url, data=data, headers=headers)
            else:
                response = requests.get(url, headers=headers)

            if response.status_code == 200:
                try:
                    return response.json()
                except:
                    return {}

            if response.status_code == 503:
                retries -= 1
                continue
            else:
                raise VultrException(
                    status_codes[response.status_code] + ': ' +
                    response.text)

        raise VultrException(status_codes[503])


class EphemeralProviderVultr:
    name = 'Vultr'

    def __init__(self, config):
        self.api_key = config['api_key']
        self.locations = config['locations']

        self.api = VultrAPI(self.api_key)

    def list_instances(self):
        instances = []

        servers = self.api.server_list(tag='ephemeralvpn')
        for server in servers:
            if server['server_state'] != 'ok' and \
                    server['power_status'] == 'running' and \
                    server['status'] == 'active':
                continue

            instances.append({
                'provider': self,
                'instance_id': server['SUBID'],
                'location': server['location'],
                'address': server['main_ip']
            })

        return instances

    def create_instance(self, location):
        dcid = self.api.name_to_dcid(location)
        planid = self.api.cheapest_vpsplanid(dcid)

        label = uuid.uuid4().hex

        self.api.request(
            'server/create',
            data={
                'DCID': dcid,
                'VPSPLANID': planid,
                'OSID': '244',
                'label': label,
                'tag': 'ephemeralvpn'
            })

        okrunningactive = 0
        while True:
            servers = self.api.server_list(label=label)
            for server in servers:
                self.log.info('creating instance {} IP {} status {}'.format(
                    'unknown',
                    server['main_ip'],
                    server['status']))

                if server['server_state'] == 'ok' and \
                        server['power_status'] == 'running' and \
                        server['status'] == 'active':
                    okrunningactive += 1
                else:
                    okrunningactive = 0

                if okrunningactive >= 6:
                    time.sleep(12)

                    self.log.info('instance is running - calling provisioner')
                    fabric_provision(
                        server['main_ip'],
                        'root',
                        server['default_password'])

                    return

            time.sleep(2)

    def suicide(self, instance):
        self.log.info('destroying instance ' + instance['instance_id'])
        self.api.request(
            'server/destroy',
            data={'SUBID': instance['instance_id']})
