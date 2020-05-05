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


from math import log
from sqlitedict import SqliteDict

# encoding/decoding functions for sqlitedict


def hll_encode(obj):
    return sqlite3.Binary(zlib.compress(pickle.dumps(obj, pickle.HIGHEST_PROTOCOL)))


def hll_decode(obj):
    return pickle.loads(zlib.decompress(bytes(obj)))


ap = argparse.ArgumentParser(
    description='calulate the magnitude from a given HLL-filei')

ap.add_argument("-f", "--hllfile",
                type=str,
                required=True,
                help='input HLL File')

# Execute the parse_args() method
args = ap.parse_args()

hllfile = args.hllfile

inputhll = SqliteDict(hllfile, encode=hll_encode, decode=hll_decode)


totals = len(inputhll['TOTAL'])
mag_scale = log(totals)/10


for tld in inputhll:
    mag = round(log(len(inputhll[tld]))/mag_scale, 2)
    print("{};{}".format(tld, mag))
