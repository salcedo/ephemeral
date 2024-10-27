import base64
import json
import tarfile

from cStringIO import StringIO

from fabric.api import env, put, run


def fabric_provisioner(host_string, user, password):
    env.host_string = host_string
    env.user = user
    env.password = password

    env.connection_attempts = 24
    env.timeout = 5

    # run('apt-get update -yq')
    # run('apt-get install -yq openvpn')
    # run('mkdir /ephemeral')

    # put('certs/*', '/ephemeral/')
    # put('init.sh', '/ephemeral/init.sh')
    # put('openvpn.conf', '/ephemeral/server.conf')
    # run('sed -i "s/group nobody/group nogroup/" /ephemeral/server.conf')

    # run('chmod +x /ephemeral/init.sh')
    # run('/ephemeral/init.sh server')
    # run('/ephemeral/init.sh firewall')
