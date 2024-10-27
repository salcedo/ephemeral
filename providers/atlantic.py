import base64
import calendar
import hashlib
import hmac
import logging
import time
import uuid

import requests

from providers.provisioner import fabric_provisioner


class EphemeralProviderAtlantic:
    name = 'Atlantic.net'

    def __init__(self, config):
        self.log = logging.getLogger('Atlantic.net')

        self.api_public_key = config['api_public_key']
        self.api_private_key = config['api_private_key']
        self.type = config['type']
        self.locations = config['locations']

    def list_instances(self):
        response = self.request({'Action': 'list-instances'})
        items = response['list-instancesresponse']['instancesSet']

        instances = []

        if items is None:
            return instances

        for item in items:
            vm = items[item]
            if vm['vm_description'] != 'ephemeralvpn' and \
               vm['vm_status'] != 'RUNNING':
                continue

            instances.append({
                'provider': self,
                'instance_id': vm['InstanceId'],
                'location': 'unknown',
                'address': vm['vm_ip_address']})

        return instances

    def create_instance(self, location):
        response = self.request({
            'Action': 'run-instance',
            'servername': 'ephemeralvpn',
            'imageid': 'debian-9.0.0_64bit',
            'planname': self.type,
            'vm_location': location,
        })

        instance = response['run-instanceresponse']['instancesSet']['item']

        while True:
            response = self.request({
                'Action': 'describe-instance',
                'instanceid': instance['instanceid']
            })['describe-instanceresponse']['instanceSet']['item']

            self.log.info('creating instance {} IP {} status {}'.format(
                instance['instancecid'],
                instance['ip_address'],
                response['vm_status']))
            time.sleep(5)

            if response['vm_status'] == 'RUNNING':
                time.sleep(10)
                break

        self.log.info('instance is running - running provisioner')
        fabric_provisioner(
            instance['ip_address'],
            instance['username'],
            instance['password'])

    def suicide(self, instance):
        self.log.info('destroying instance ' + instance['instance_id'])
        return self.request({
            'Action': 'terminate-instance',
            'instanceid': instance['instance_id']
        })

    def request(self, params):
        endpoint = 'https://cloudapi.atlantic.net/?'

        epoch = str(int(calendar.timegm(time.gmtime())))
        rndguid = uuid.uuid4().hex

        digest = hmac.new(
            self.api_private_key.encode(),
            msg=(epoch + rndguid).encode(),
            digestmod=hashlib.sha256).digest()

        signature = base64.b64encode(digest).decode()

        p = {
            'Version': '2010-12-30',
            'ACSAccessKeyId': self.api_public_key,
            'Format': 'json',
            'Timestamp': epoch,
            'Rndguid': rndguid,
            'Signature': signature,
        }

        for param in params:
            p[param] = params[param]

        return requests.get(endpoint, params=p).json()
