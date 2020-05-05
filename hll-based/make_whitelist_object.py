#!/usr/bin/env python3
#
# Copyright (c) 2020 Internet Corporation for Assigned Names and Numbers (ICANN)
#
# Created by nic.at GmbH under contract with ICANN.
#
# generates the whitelistobject for ICANN DNS Magnitude Calculation
#
# input (stdin) : uniq -c out ala
#
#    2 !!u!4c
#    1 !+adbhkovp\032xtjhjgm4a
#    1 !-4azz\235\138\149-com
#
# reads the lines, checks if number of files (1st column) bigger than limit,
# if yes tld (2nd column) is added to a set-object
#
# when finished the set object is stored on disk (file "whitelistfile")
#

import sys
import pickle
import argparse

ap = argparse.ArgumentParser(
    description='generates whitelist object for dns magnitude calculation. reads "uniq -c" output from stdin and check if number of filees (1st column) bigger than limit')

# Add the arguments
ap.add_argument("-o", "--outputfile",
                type=str,
                required=True,
                help='the outfile to store the whitelist object')

ap.add_argument("-l", "--limit",
                type=int,
                required=True,
                help='the limit, only entries bigger than limit will be added to the whitelist')

args = ap.parse_args()

limit = args.limit    # number of file in which a tld must be found
whitelistfile = args.outputfile

whitelist = set()
for line in sys.stdin:
    lst = line.strip().split(' ')
#    if len(lst)> 1:
    try:
        (count, tld) = lst
    except ValueError:  # root zone is empty string
        count = lst[0]
        tld = '.'

    if len(tld) > 1:
        tld = tld.rstrip('.')

    if int(count) > limit:
        whitelist.add(tld)

pickle.dump(whitelist, open(whitelistfile, "wb"))

print("Added {} elements to whitelist".format(len(whitelist)))
