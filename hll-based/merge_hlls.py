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


ap = argparse.ArgumentParser(
    description='merges given HLL-file into one outputfile and calculates the magnitude')

# Add the arguments
ap.add_argument("-o", "--outputfile",
                type=str,
                required=True,
                help='file to store the merges HLLs (will be overwritten if exists)')

ap.add_argument("-r", "--reset",
                action='store_true',
                help='reset outputfile before adding new hlls')
ap.set_defaults(feature=False)

ap.add_argument('file',
                type=str,
                nargs='+',
                help='file(s) to be merged')


# Execute the parse_args() method
args = ap.parse_args()

outputfile = args.outputfile
files = args.file
reset = args.reset


if reset:
    flag = 'w'
else:
    flag = 'c'

mergehll = SqliteDict(outputfile, flag=flag, journal_mode='MEMORY',
                      encode=hll_encode, decode=hll_decode)

mergekeys = set()
for k in mergehll.keys():
    mergekeys.add(k)

for f in files:
    if not os.path.exists(f):
        print("{}: File not found".format(f))
        sys.exit()
    filehll = SqliteDict(f, encode=hll_encode, decode=hll_decode)
    # merge into outputfile
    for tld, tldhll in filehll.iteritems():
        if tld in mergekeys:   # key already in outputfile -> merge
            hll = mergehll[tld]
            if not hll.__eq__(tldhll):  # merge only if HLL is different
                hll.update(tldhll)
                mergehll[tld] = hll
        else:                   # new key in outfile -> copy
            mergehll[tld] = filehll[tld]
            mergekeys.add(tld)
    filehll.close()
    print("Total TLDs {}".format(len(mergehll)))
    print("Total IPs {}".format(len(mergehll['TOTAL'])))
mergehll.commit()
mergehll.close()
