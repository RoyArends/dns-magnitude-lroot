#!/bin/bash
#
# Copyright (c) 2020 Internet Corporation for Assigned Names and Numbers (ICANN)
#
# Created by nic.at GmbH under contract with ICANN.

rm totals.hll

for f in hlls/*.hll; do 
	echo $f
	./merge_hlls.py -o totals.hll $f
done
~                     
