#!/usr/bin/env python3
#
# Copyright (c) 2020 Internet Corporation for Assigned Names and Numbers (ICANN)
#
# Created by nic.at GmbH under contract with ICANN.

import os
import csv
import sys
import pickle
import argparse
import ipaddress
import hyperloglog
import sqlite3
import zlib

from sqlitedict import SqliteDict

# encoding/decoding functions for sqlitedict
def hll_encode(obj):
    return sqlite3.Binary(zlib.compress(pickle.dumps(obj, pickle.HIGHEST_PROTOCOL)))
def hll_decode(obj):
    return pickle.loads(zlib.decompress(bytes(obj)))

hll_error_rate=0.01
ap = argparse.ArgumentParser(
    description='reads a given royparse file and counts the number of unique hosts and unique hosts per tld in whitelist')

# Add the arguments
ap.add_argument("-i", "--inputfile",
                type=str,
		required=True,
                help='the royparse file to parse')

ap.add_argument("--whitelist",
                type=str,
                required=True,
                help='file with the stored whitelist object')

ap.add_argument("--hlloutputfile",
                type=str,
                required=True,
                help='filename to store HLL')

ap.add_argument("--aggregate",
                action='store_true',
                help='aggregate IPv4 to /24 and IPv6 to /48, default false')
ap.set_defaults(feature=False)

ap.add_argument("--ipv4only",
                action='store_true',
                help='count only IPv4 requests')
ap.set_defaults(feature=False)

ap.add_argument("--ipv6only",
                action='store_true',
                help='count only IPv6 requests')
ap.set_defaults(feature=False)


# Execute the parse_args() method
args = ap.parse_args()

inputfile = args.inputfile
whitelistfile = args.whitelist
hlloutputfile = args.hlloutputfile
aggregate = args.aggregate
ipv4only = args.ipv4only
ipv6only = args.ipv6only

if ipv4only and ipv6only:
    print('--ipv4only and --ipv6only could not be combined. PLease choose only one.')
    sys.exit()

if not inputfile == '-' and not os.path.isfile(inputfile):
    print('The inputfile does not exist')
    sys.exit()

if not os.path.isfile(whitelistfile):
    print('The whitelistfile does not exist')
    sys.exit()

# readwhitelistfile
whitelist = pickle.load(open(whitelistfile, "rb"))

# prepare HLLs
totalips = hyperloglog.HyperLogLog(hll_error_rate)
nonwhitelist = hyperloglog.HyperLogLog(hll_error_rate)
tldhll = dict()

# cache processed ips to speedup
ip_cache = dict()

if inputfile == '-':
    royparsereader = csv.reader(
        sys.stdin, delimiter=',', quoting=csv.QUOTE_MINIMAL)
else:
    royparsereader = csv.reader(
        open(inputfile), delimiter=',', quoting=csv.QUOTE_MINIMAL)

count = 0
match = 0
non_whitelist_match = 0
for (ip, fqdntld, type, size, flags) in royparsereader:
    count += 1
    tld = fqdntld[:-1].split('.')[-1]  # remove trailing dot and get tld
    ipaddr = ip.split(' ')[-1]
    agg_ip=''
    if ipaddr in ip_cache:
        agg_ip=ip_cache[ipaddr]
    else:
        ip=ipaddress.ip_address(ipaddr)
        if ip.version==4 and not ipv6only: # count only ipv4
            if aggregate:
                agg_ip=str(ipaddress.ip_network(ipaddr+'/24',False))
                ip_cache[ipaddr]=str(agg_ip)
            else:
                ip_cache[ipaddr]=ipaddr
                agg_ip=ipaddr
        elif ip.version==6 and not ipv4only:   # count only ipv6
            if aggregate:
                agg_ip=str(ipaddress.ip_network(ipaddr+'/48',False))
                ip_cache[ipaddr]=str(agg_ip)
            else:
                ip_cache[ipaddr]=ipaddr
                agg_ip=ipaddr

    totalips.add(agg_ip)
    if tld == '':
        tld = '.'
    if tld in whitelist:
        if tld not in tldhll.keys():
            tldhll[tld] = hyperloglog.HyperLogLog(hll_error_rate)
        match += 1
        tldhll[tld].add(agg_ip)
    else:
        nonwhitelist.add(agg_ip)

# save HLLs to hllfile
tldhll['TOTAL'] = totalips
tldhll['NONWHITELIST_TLDS'] = nonwhitelist

with SqliteDict(hlloutputfile, flag='w',encode=hll_encode, decode=hll_decode) as outdict:
    for tld in tldhll:
        outdict[tld]=tldhll[tld]
    outdict.commit()

print("Parsed {} lines".format(count))
print("Found {} whitelistes lines".format(match))
print("Found {} TLDs".format(len(tldhll)))
print("Found {} IPs for non-whitelisted TLDs".format(len(nonwhitelist)))
print("Found {} different IPs".format(len(totalips)))
