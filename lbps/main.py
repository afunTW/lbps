#   simulation parameter:
#       #RN: 6
#       #UE: 40 on each RN
#       channel capacity: 20 MHz (#RB=100)
#       type of UE:
#           H-type: CQI=10~15
#           M-tpye: CQI=7~9
#           L-tpye: CQI=1~6
#       packet size: 800 bits
#       DATA_TH: estimated_system_capacity*0.8
#       PROB_TH: 0.8

#   DRX parameter:
#       on duration: 1 ms
#       inactivity timer: 10 ms
#       short DRX cycle: 40 ms
#       short cycle timer: 2
#       long DRX cycle: 160 ms

#   PSE = sleep_time / (active_time + sleep_time)
#   avgDelay = sum(delay)/n

import random
import copy
from LBPS import *  #   include TopDown and BottomUp algorithm

class RN(object):
    def __init__(self, id):
        self.__id= id;
    @property
    def RUE(self):
        return self.__RUE;
    @RUE.setter
    def RUE(self, RUE):
        self.__RUE= RUE;

class UE(object):
    def __init__(self, id, CQI):
        self.__id= id;
        self.__CQI= CQI;

if __name__ == '__main__':

    # l_RN: list of RN
    l_RN= [RN(count) for count in range(0,6)];

    # assign 40 UE with random CQI to each RN
    for i in range(length(l_RN)):
        l_RN[i].RUE= [UE(i, random.randint(1,15)) for i in range(0,40)];

    # 6 revised LBPS scheduling
    TDAggrRN= copy.deepcopy(l_RN);
    TDSplitRN= copy.deepcopy(l_RN);
    TDMergeRN= copy.deepcopy(l_RN);
    BUAggrMin= copy.deepcopy(l_RN);
    BUSplitMin= copy.deepcopy(l_RN);
    BUMergeMerge= copy.deepcopy(l_RN);

    # result
    TDAggrRN= LBPS.TopDownAggr(TDAggrRN);
    TDSplitRN= LBPS.TopDownSplit(TDSplitRN);
    TDMergeRN= LBPS.TopDownMergeRN(TDMergeRN);
    BUAggrMin= LBPS.BottomUpAggrMin(BUAggrMin);
    BUSplitMin= LBPS.BottomUpSplitMin(BUSplitMin);
    BUMergeMerge= LBPS.BottomUpMergeMerge(BUMergeMerge);
