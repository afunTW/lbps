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
	relays[i].connect(status='D', interface='access', bandwidth=BANDWIDTH, CQI_type=['M', 'H'], flow='VoIP')
	relays[i].capacity

"""[summary] apply LBPS algorithm

[description]
"""
TestAggrRN = copy.deepcopy(relays[0])
aggr(TestAggrRN, 'access')
TestSplitRN = copy.deepcopy(relays[0])
split(TestSplitRN, 'access')
# TestMergeRN = copy.deepcopy(relays[0])
# merge(TestMergeRN, 'access')

# # 6 revised LBPS scheduling
# TDAggrRN= copy.deepcopy(relays);
# TDSplitRN= copy.deepcopy(relays);
# TDMergeRN= copy.deepcopy(relays);
# BUAggrMin= copy.deepcopy(relays);
# BUSplitMin= copy.deepcopy(relays);
# BUMergeMerge= copy.deepcopy(relays);
#
# # result
# TDAggrRN= LBPS.TopDownAggr(TDAggrRN);
# TDSplitRN= LBPS.TopDownSplit(TDSplitRN);
# TDMergeRN= LBPS.TopDownMergeRN(TDMergeRN);
# BUAggrMin= LBPS.BottomUpAggrMin(BUAggrMin);
# BUSplitMin= LBPS.BottomUpSplitMin(BUSplitMin);
# BUMergeMerge= LBPS.BottomUpMergeMerge(BUMergeMerge);
