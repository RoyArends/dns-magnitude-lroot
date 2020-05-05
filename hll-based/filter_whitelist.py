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

ap = argparse.ArgumentParser(
    description='reads "royparse format" files from STDIN, matches TLD against whitelist and print line if tld matched to STDOUT')

# Add the arguments
ap.add_argument("--whitelist",
                type=str,
                required=True,
                help='file with the stored whitelist object')

# Execute the parse_args() method
args = ap.parse_args()

whitelistfile = args.whitelist

if not os.path.isfile(whitelistfile):
    print('The whitelistfile does not exist')
    sys.exit()

# readwhitelistfile
whitelist = pickle.load(open(whitelistfile, "rb"))

infilereader = csv.reader(
    sys.stdin, delimiter=',', quoting=csv.QUOTE_MINIMAL)

count = 0
match = 0
non_whitelist_match = 0
oldtld = None
# for (ip, tld) in infilereader:

for (ip, fqdntld, type, size, flags) in infilereader:
    tld = fqdntld[:-1].split('.')[-1]  # remove trailing dot and get tld
    ipaddr = ip.split(' ')[-1]
    if tld in whitelist:
        print("{},{}".format(ipaddr, tld))
