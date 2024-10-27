#!/bin/bash

if [ "$1" == "firewall" ]; then
    EXT_IF=$(ip route show | grep default | sed 's/.*dev \([a-z0-9]*\).*/\1/' | head -1)

    sysctl -w net.ipv4.ip_forward=1
    iptables -t nat -A POSTROUTING -o $EXT_IF -j MASQUERADE

    iptables -A INPUT -i $EXT_IF -p udp --dport 51194 -j ACCEPT
    iptables -A INPUT -i $EXT_IF -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
    iptables -A INPUT -i $EXT_IF -j DROP
else
    openvpn --cd /ephemeral --config server.conf --daemon
fi
