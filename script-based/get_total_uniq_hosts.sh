#!/bin/bash
#
# Copyright (c) 2020 Internet Corporation for Assigned Names and Numbers (ICANN)
#
# Created by nic.at GmbH under contract with ICANN.

awk -F'[ ,]' '{ print $2 }' | sort | uniq | wc -l
