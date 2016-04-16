#!/usr/bin/python3

from __init__ import *

"""[summary] init

[description]
1. 6 RNs, 240 UEs with given buffer
2. build up bearer between two devices
3. calculate capacity
"""

# base_station = eNB(M_BUF)
relays = [RN(M_BUF) for i in range(6)]
users = [UE(M_BUF) for i in range(240)]

for i in range(len(relays)):
	relays[i].childs = users[i*40:i*40+40]
	relays[i].connect(status='D', interface='access', bandwidth=BANDWIDTH, CQI_type=['M', 'H'], flow='Video')
	relays[i].capacity

# LBPS-Aggr, Split, Merge
TestAggrRN = copy.deepcopy(relays[0])
aggr(TestAggrRN, 'access')
TestSplitRN = copy.deepcopy(relays[0])
split(TestSplitRN, 'access')
TestMergeRN = copy.deepcopy(relays[0])
merge(TestMergeRN, 'access')

# TDD