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

# # LBPS-Aggr, Split, Merge
# TestAggrRN = copy.deepcopy(relays[0])
# aggr(TestAggrRN, 'access')
# result = scheduling_result(TestAggrRN, 'aggr', show=True)

# TestSplitRN = copy.deepcopy(relays[0])
# split(TestSplitRN, 'access')
# result = scheduling_result(TestSplitRN, 'split', show=True)

# TestMergeRN = copy.deepcopy(relays[0])
# merge(TestMergeRN, 'access')
# result = scheduling_result(TestMergeRN, 'merge', show=True)

# LBPS with TDD
TDD_config = ONE_HOP_TDD_CONFIG[1]

# TestAggrRN = copy.deepcopy(relays[0])
# TestAggrRN.tdd_config = TDD_config
# aggr(TestAggrRN, 'access')
# result = scheduling_result(TestAggrRN, 'aggr', show=True)


TestMergeRN = copy.deepcopy(relays[0])
TestMergeRN.tdd_config = TDD_config
merge(TestMergeRN, 'access')
result = scheduling_result(TestMergeRN, 'merge', show=True)

M3(TestMergeRN, 'access', result)

# pre = "%s::TDD::VSC\t\t" % TestAggrRN.name
# msg_execute("virtual capacity = %d" % TestAggrRN.virtualCapacity['access'], pre=pre)

# TestTDD = copy.deepcopy(relays[0])
# TestTDD.tdd_config = TDD_config

# pre = "%s::TDD::VSC\t\t" % TestTDD.name
# msg_execute("CQI = %d" % TestTDD.link['access'].CQI, pre=pre)
# msg_execute("virtual capacity = %d" % TestTDD.virtualCapacity['access'], pre=pre)

# for i in TestTDD.childs:
# 	pre = "%s::TDD::VSC\t\t" % i.name

# 	i.tdd_config = TDD_config
# 	msg_execute("CQI = %d" % i.link['access'][0].CQI, pre=pre)
# 	msg_execute("virtual capacity = %d" % i.virtualCapacity['access'], pre=pre)
