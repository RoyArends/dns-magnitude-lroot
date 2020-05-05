#!/bin/bash
#
# Copyright (c) 2020 Internet Corporation for Assigned Names and Numbers (ICANN)
#
# Created by nic.at GmbH under contract with ICANN.

awk -F'[ ,]' '{n=split($3,L,"."); if ($3==".") {L[n-1]="."}; print L[n-1] " " $2 }' | sort | uniq -c  | awk -F ' ' '{print $2}' | sort | uniq -c 
