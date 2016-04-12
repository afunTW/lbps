#!/usr/bin/python3

from __init__ import *

"""
init
# 6 RNs, 240 UEs with given buffer
# build up bearer between two devices
# calculate capacity
"""

# base_station = eNB(M_BUF)
relays = [RN(M_BUF) for i in range(6)]
users = [UE(M_BUF) for i in range(240)]

for i in range(len(relays)):
	relays[i].childs = users[i*40:i*40+40]
	relays[i].connect(status='D', interface='access', bandwidth=BANDWIDTH, CQI_type=['M', 'H'], flow='VoIP')
	relays[i].capacity

# # Test: assign UE to RN
# for i in relays:
# 	parent = type(i).__name__ + "[" + str(i.id) + "]"
# 	print("\n\n%s:\t" % parent)
# 	for j in i.childs:
# 		child = type(j).__name__ + str(j.id)
# 		print("\n%s:\tCQI= %d\t lambda= %f" % (child, j.link['access'][0].CQI, j.lambd['access']), end='')

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
