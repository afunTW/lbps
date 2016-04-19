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

# LBPS-Aggr, Split, Merge
TestAggrRN = copy.deepcopy(relays[0])
aggr(TestAggrRN, 'access')
TestSplitRN = copy.deepcopy(relays[0])
split(TestSplitRN, 'access')
TestMergeRN = copy.deepcopy(relays[0])
merge(TestMergeRN, 'access')

# TDD
TDD_config = ONE_HOP_TDD_CONFIG[1]
TestTDD = copy.deepcopy(relays[0])
TestTDD.tdd_config = TDD_config

me = type(TestTDD).__name__ + str(TestTDD.id)
pre = "%s::TDD::VSC\t\t" % me
# msg_execute("CQI = %d" % TestTDD.link['access'].CQI, pre=pre)
msg_execute("virtual capacity = %d" % TestTDD.virtualCapacity['access'], pre=pre)

for i in TestTDD.childs:
	me = type(i).__name__ + str(i.id)
	pre = "%s::TDD::VSC\t\t" % me

	i.tdd_config = TDD_config
	msg_execute("CQI = %d" % i.link['access'][0].CQI, pre=pre)
	msg_execute("virtual capacity = %d" % i.virtualCapacity['access'], pre=pre)
