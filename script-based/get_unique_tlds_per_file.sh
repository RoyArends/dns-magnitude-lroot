#!/bin/bash
#
# Copyright (c) 2020 Internet Corporation for Assigned Names and Numbers (ICANN)
#
# Created by nic.at GmbH under contract with ICANN.

cd /data/curated/20190601/

for d in *.l.dns.icann.org; do
	cd $d
	for f in *.cbor; do
		echo $f
		cat $f |  awk -F'[ ,]' '{n=split($3,L,"."); if ($3==".") {L[n-1]="."}; print L[n-1] }' |  awk '$1 ~ /^[a-z\-]+$/ { print $1 }' |  sort | uniq > $f.unique_tlds
	done
	pwd
	cd ..
done
