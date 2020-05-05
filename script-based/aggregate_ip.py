#!/usr/bin/python3 -u
#
# Copyright (c) 2020 Internet Corporation for Assigned Names and Numbers (ICANN)
#
# Created by nic.at GmbH under contract with ICANN.

import csv
import sys
import ipaddress

inputreader = csv.reader(
    sys.stdin, delimiter=',', quoting=csv.QUOTE_MINIMAL)

ip_cache = dict()

for line in inputreader:
    flags, ipaddr = line[0].split(' ')
    agg_ip = ''
    if ipaddr in ip_cache:
        agg_ip = ip_cache[ipaddr]
    else:
        ip = ipaddress.ip_address(ipaddr)
        if ip.version == 4:
            agg_ip = str(ipaddress.ip_network(ipaddr+'/24', False))
            ip_cache[ipaddr] = str(agg_ip)
        elif ip.version == 6:   # count only ipv6
            agg_ip = str(ipaddress.ip_network(ipaddr+'/48', False))
            ip_cache[ipaddr] = str(agg_ip)
    print("{} {},{},{},{},{}".format(
        flags, agg_ip, line[1], line[2], line[3], line[4]))
