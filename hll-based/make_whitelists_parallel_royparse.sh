#!/bin/bash
#
# Copyright (c) 2020 Internet Corporation for Assigned Names and Numbers (ICANN)
#
# Created by nic.at GmbH under contract with ICANN.

# place to store result files
OUTPUTDIR=/data/processed/whitelists

export LC_ALL=C

DIR="$(dirname "${BASH_SOURCE[0]}")"

cd /data/curated/

for day in */; do
	if [ -f "$OUTPUTDIR/${day::-1}-whitelist.pickle" ]; then
		continue
	fi
	echo "Processing $day"
	cd $day
	for d in */; do
		cd $d
		mkdir -p $OUTPUTDIR/$day/$d
		find . -type f |  parallel --will-cite -j 10 "zcat {} |  awk -F'[ ,]' '{n=split(\$3,L,\".\"); if (\$3==\".\") {L[n-1]=\".\"}; tld=L[n-1]; if (tld ~ /^[a-z\-]+$/ && !a[tld]++) {print (tld);}}' | LANG=C sort -S 2G --parallel=8 > $OUTPUTDIR/$day/$d/{}.unique_tlds"
		cd ..
	done
	find $OUTPUTDIR/$day -type f -exec cat {} + | LANG=C sort  -S 16G --parallel=8  | uniq -c | $DIR/make_whitelist_object.py -l 30 -o  $OUTPUTDIR/${day::-1}-whitelist.pickle
	cd ..
	rm -r $OUTPUTDIR/$day
done
