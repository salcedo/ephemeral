import uuid

import boto3
import requests

from providers.provisioner import fabric_provisioner


class EphemeralProviderAWS:
    name = 'Amazon EC2'

    def __init__(self, config):
        self.aws_access_key_id = config['aws_access_key_id']
        self.aws_secret_access_key = config['aws_secret_access_key']
        self.type = config['type']
        self.locations = config['locations']

    def list_instances(self):
        instances = []
        for location in self.locations:
            ec2 = self.resource('ec2', location)
            items = ec2.instances.filter(
                Filters=[{'Name': 'instance-state-name',
                          'Values': ['running']},
                         {'Name': 'tag:Role',
                          'Values': ['ephemeral']}])

            for instance in items:
                instances.append({
                    'provider': self,
                    'instance_id': instance.instance_id,
                    'location': location,
                    'address': instance.public_ip_address})

        return instances

    def create_instance(self, location):
        ec2 = self.resource('ec2', location)

        vpc = ec2.create_vpc(CidrBlock='172.22.0.0/16')
        print('[+AWS] Created VPC in ' + location)
        subnet = vpc.create_subnet(CidrBlock='172.22.42.0/24')
        print('[+AWS] Created subnet in ' + location)
        gateway = ec2.create_internet_gateway()
        print('[+AWS] Created internet gateway in ' + location)
        vpc.attach_internet_gateway(
            InternetGatewayId=gateway.id,
            VpcId=vpc.id)

        for r in vpc.route_tables.all():
            rtb = ec2.RouteTable(r.id)
        rtb.create_route(
            DestinationCidrBlock='0.0.0.0/0',
            GatewayId=gateway.id)
        rtb.associate_with_subnet(SubnetId=subnet.id)

        print('[+AWS] Created route table and associations in ' + location)
        sg = ec2.create_security_group(
            Description='ephemeral',
            GroupName=uuid.uuid4().hex,
            VpcId=vpc.id)
        sg.authorize_ingress(
            CidrIp='0.0.0.0/0',
            FromPort=22,
            ToPort=22,
            IpProtocol='tcp')
        sg.authorize_ingress(
            CidrIp='0.0.0.0/0',
            FromPort=1194,
            ToPort=1194,
            IpProtocol='udp')

        print('[+AWS] Created security group in ' + location)

        ec2.create_instances(
            ImageId=self.get_debian_ami(location),
            InstanceType=self.type,
            MinCount=1,
            MaxCount=1,
            NetworkInterfaces=[
                {
                    'DeviceIndex': 0,
                    'SubnetId': subnet.id,
                    'Groups': [sg.id],
                    'AssociatePublicIpAddress': True
                }
            ],
            TagSpecifications=[
                {
                    'ResourceType': 'instance',
                    'Tags': [
                        {
                            'Key': 'Role',
                            'Value': 'ephemeral'
                        }
                    ]
                }
            ])

        print('[+AWS] Created instance in ' + location)

    def suicide(self, instance):
        ec2 = self.resource('ec2', instance['location'])

        inst = list(
            ec2.instances.filter(
                InstanceIds=[instance['instance_id']]
            )
        )[0]

        gateway = None
        for igw in ec2.internet_gateways.all():
            for attachment in igw.attachments:
                if attachment['VpcId'] == inst.vpc_id:
                    gateway = igw
                    break

        sg = ec2.SecurityGroup(inst.security_groups[0]['GroupId'])
        subnet = ec2.Subnet(inst.subnet_id)
        vpc = ec2.Vpc(inst.vpc_id)

        ec2.instances.filter(
            InstanceIds=[instance['instance_id']]).terminate()
        inst.wait_until_terminated()

        print('[-AWS] Terminated instance in ' + instance['location'])
        gateway.detach_from_vpc(VpcId=vpc.id)
        gateway.delete()
        sg.delete()
        subnet.delete()
        vpc.delete()

        print('[-AWS] Removed VPC from ' + instance['location'])

    def resource(self, resource_name, location):
        return boto3.resource(
            resource_name,
            aws_access_key_id=self.aws_access_key_id,
            aws_secret_access_key=self.aws_secret_access_key,
            region_name=location)

    def get_debian_ami(self, location):
        url = 'https://wiki.debian.org/Cloud/AmazonEC2Image/Stretch?action=raw'
        debian_amazonec2image = requests.get(url).text

        parsing = False
        amis = {}
        for line in debian_amazonec2image.splitlines():
            if line.startswith('== Stretch '):
                parsing = True

            if parsing is True:
                if line.startswith('||'):
                    fields = line.split(' ')

                    if not fields[1].startswith("'"):
                        amis[fields[1]] = fields[3]

        return amis[location]
