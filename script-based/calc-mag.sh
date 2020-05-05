#!/bin/bash
#
# Copyright (c) 2020 Internet Corporation for Assigned Names and Numbers (ICANN)
#
# Created by nic.at GmbH under contract with ICANN.

./get_tld_counters.sh | awk -v totalhosts="$TOTALHOSTS" 'BEGIN { mag_scale=log(totalhosts)/10;print "SCALE " mag_scale " " totalhosts;}  {mag=log($1)/mag_scale; print $2 " " mag " " $1 }' | sort -r  -k2,2 -g
