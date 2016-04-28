#!/usr/bin/python3

from __init__ import *
from pprint import pprint

"""[summary] init

[description]
1. 6 RNs, 240 UEs with given buffer
2. build up bearer between two devices
3. calculate capacity
"""

base_station = eNB(M_BUF)
relays = [RN(M_BUF) for i in range(6)]
users = [UE(M_BUF) for i in range(240)]

for i in range(len(relays)):
	relays[i].childs = users[i*40:i*40+40]
	relays[i].connect(status='D', interface='access', bandwidth=BANDWIDTH, CQI_type=['M', 'H'], flow='Video')
	relays[i].parent = base_station
	base_station.childs.append(relays[i])

base_station.connect(status='D', interface='backhaul', bandwidth=BANDWIDTH, CQI_type=['H'], flow='Video')

"""[summary] LBPS basic scheme

[description]
1. Aggr
2. Split
3. Merge
"""

# TestAggrRN = copy.deepcopy(relays[0])
# K = aggr(TestAggrRN, 'access')
# result = scheduling_result(TestAggrRN, 'aggr', show=True)

# TestSplitRN = copy.deepcopy(relays[0])
# K = split(TestSplitRN, 'access')
# result = scheduling_result(TestSplitRN, 'split', show=True)

# TestMergeRN = copy.deepcopy(relays[0])
# K = merge(TestMergeRN, 'access')
# result = scheduling_result(TestMergeRN, 'merge', show=True)

"""[summary] LBPS basic scheme with TDD

[description]
1. Aggr in TDD
2. Split in TDD
3. Merge in TDD

only RN will be assign TDD configuration so far

"""

TDD_config = ONE_HOP_TDD_CONFIG[1]

TestAggrRN = copy.deepcopy(relays[0])
TestAggrRN.tdd_config = TDD_config
K = aggr(TestAggrRN, 'access', 'TDD')
result = scheduling_result(TestAggrRN, 'aggr', show=False)
map_result = M3(TestAggrRN, 'access', result)

result = scheduling_result(TestAggrRN, 'aggr', result=result, map_result=map_result, TDD=True, show=True)

TestSplitRN = copy.deepcopy(relays[0])
TestSplitRN.tdd_config = TDD_config
K = split(TestSplitRN, 'access', 'TDD')
result = scheduling_result(TestSplitRN, 'split', show=False)
map_result = M3(TestSplitRN, 'access', result)

result = scheduling_result(TestSplitRN, 'split', result=result, map_result=map_result, TDD=True, show=True)

TestMergeRN = copy.deepcopy(relays[0])
TestMergeRN.tdd_config = TDD_config
K = merge(TestMergeRN, 'access', 'TDD')
result = scheduling_result(TestMergeRN, 'merge', show=False)
map_result = M3(TestMergeRN, 'access', result)

result = scheduling_result(TestMergeRN, 'merge', result=result, map_result=map_result, TDD=True, show=True)