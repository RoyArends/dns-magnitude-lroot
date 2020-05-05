#!/bin/bash
#
# Copyright (c) 2020 Internet Corporation for Assigned Names and Numbers (ICANN)
#
# Created by nic.at GmbH under contract with ICANN.

INPUTDIR=/data/curated
OUTPUTDIR=/data/processed/mag
# take only tlds with more than $LIMT unique requests into calculation
LIMIT=99
DAY=$1

# avoid perl locale warnings and speedup sort
export LANG=C

mkdir -p $OUTPUTDIR


# zcat all gzipped files from day (10 in parallel) filter only a-z strings and convert into "new format"
find $INPUTDIR/$DAY/*/  -type f | parallel --will-cite --line-buffer -j 10 "zcat -f {} |  awk -F '[ ,]' '{n=split(\$3,L,\".\"); if (\$3==\".\") {L[n-1]=\".\"}; print \$2 \",\" L[n-1] }' " |
    # feed into to pipes
    tee  >( 
    # 1st leg: count the unique ips per day 
    #sort -u outputs only one row per sort column, so we do not need do parse the ip first
       sort -u -S 8G --parallel=8  -k 1,1 -t , | wc -l > $OUTPUTDIR/$DAY.total) |
    # 2nd leg: get ip,tld tuples
        sort -S 24G --parallel=16 -k 2,2 -k 1,1 -t , | 
            tee >(
                #1st leg: count total requests per tld
                awk -F , '{print $2;}' | uniq -c | awk -v limit="$LIMIT" -v day="$DAY" 'BEGIN {print "date,tld,querycount";}  { if ($1 > limit) {print day "," $2 "," $1;} }' | (sed -u 1q ; sort -r  -k3,3 -g -t ,) > $OUTPUTDIR/$DAY.querycounts  ) |
                #2nd leg: get uniq ip,tld tuples and use only tld
                uniq | awk -F , '{print $2;}' | 
                #count per tld and take only tlds with more than $LIMIT requests 
                    uniq -c | awk -v limit="$LIMIT" ' { if ($1 > limit) {print $0;} }' > $OUTPUTDIR/$DAY.tldcounts 
            #end inner tee
    #end tee

# now lets calc the magnitudes

TOTALHOSTS=`cat $OUTPUTDIR/$DAY.total`
cat $OUTPUTDIR/$DAY.tldcounts | awk -v totalhosts="$TOTALHOSTS" -v day="$DAY" 'BEGIN { mag_scale=log(totalhosts)/10;print "date,tld,magnitude,uniquehosts";print day ",TOTALUNIQUEHOSTS,," totalhosts;}  {mag=log($1)/mag_scale; print day "," $2 "," mag "," $1 }' | (sed -u 1q ; sort -r  -k3,3 -g -t ,)  > $OUTPUTDIR/$DAY.mags

# remove tmp files
#rm $OUTPUTDIR/$DAY.tldcounts
#rm $OUTPUTDIR/$DAY.total



