#!/usr/bin/python3

from __init__ import *

"""
# init
#   deploy 6 RNs and 40 UEs for each RN (total 240 UE)
#   declare UEs with random CQI to each RN
#   aggregate UE info then assign to RN
"""

l_RN= [RN(buf=H_BUF, bandwidth=BANDWIDTH, CQI=10, flow='VoIP') for count in range(0,6)];
for i in l_RN:
    i.add_UE(40, ['M', 'H'], buf=H_BUF, bandwidth=BANDWIDTH, flow='VoIP')

# # Test: assign UE to RN
# for i in range(0,len(l_RN)):
#     print("\nRN[%d]:\t" % i)
#     for j in range(0, len(l_RN[i].RUE)):
#         print("\tUE[%d].link.CQI= %d" %(j, l_RN[i].RUE[j].link.CQI), end='')
#         if j%5 is 4: print()

# # Test: print all value of RN
# print("RN[0]: ")
# print("DL buffer\t\t" + str(l_RN[0].buf['D']) + "bits")
# print("status\t\t\t" + l_RN[0].status)
# print("Channel\t\t\t" + str(l_RN[0].link))
# print("Channel.interface\t" + l_RN[0].link.interface)
# print("Channel.bandwidth\t" + str(l_RN[0].link.bandwidth))
# print("Channel.CQI\t\t" + str(l_RN[0].link.CQI))
# print("Channel.flow\t\t" + l_RN[0].link.flow)
# print("Channel.bitrate\t\t" + str(l_RN[0].link.bitrate))
# print("Channel.pkt_size\t" + str(l_RN[0].link.pkt_size))
# print("Channel.delay_budget\t" + str(l_RN[0].link.delay_budget))
# print("RUE len\t\t\t" + str(len(l_RN[0].RUE)))

# # 6 revised LBPS scheduling
# TDAggrRN= copy.deepcopy(l_RN);
# TDSplitRN= copy.deepcopy(l_RN);
# TDMergeRN= copy.deepcopy(l_RN);
# BUAggrMin= copy.deepcopy(l_RN);
# BUSplitMin= copy.deepcopy(l_RN);
# BUMergeMerge= copy.deepcopy(l_RN);
#
# # result
# TDAggrRN= LBPS.TopDownAggr(TDAggrRN);
# TDSplitRN= LBPS.TopDownSplit(TDSplitRN);
# TDMergeRN= LBPS.TopDownMergeRN(TDMergeRN);
# BUAggrMin= LBPS.BottomUpAggrMin(BUAggrMin);
# BUSplitMin= LBPS.BottomUpSplitMin(BUSplitMin);
# BUMergeMerge= LBPS.BottomUpMergeMerge(BUMergeMerge);
