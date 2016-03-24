#!/usr/bin/python3

import random
import copy
from device import UE, RN, eNB
# from LBPS import *  #   include TopDown and BottomUp algorithm

# init
#   deploy 6 RNs and 40 UEs for each RN (total 240 UE)
#   declare UEs with random CQI to each RN
#   aggregate UE info then assign to RN

l_RN= [RN() for count in range(0,6)];
for i in range(len(l_RN)):
    l_RN[i].RUE= [UE(CQI=random.randint(1,15), parentDevice= i) for i in range(0,40)];

# Test: assign UE to RN
for i in range(0,len(l_RN)):
    print("\nRN[%d]:\t" % i)
    for j in range(0, len(l_RN[i].RUE)):
        print("\tUE[%d].CQI= %d" %(j, l_RN[i].RUE[j].CQI), end='')
        if j%5 is 4: print()

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
