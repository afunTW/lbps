#!/usr/bin/python3

from __init__ import *
from pprint import pprint

# create device instance
base_station = eNB(M_BUF)
relays = [RN(M_BUF) for i in range(6)]
users = [UE(M_BUF) for i in range(240)]

# assign the relationship and CQI
base_station.childs = relays
for i in range(len(relays)):
	relays[i].childs = users[i*40:i*40+40]
	relays[i].parent = base_station
	relays[i].CQI = ['H']
	for j in range(i*40, i*40+40):
		users[j].parent = relays[i]
		users[j].CQI = ['M', 'H']

# build up the bearer
for i in base_station.childs:
	base_station.connect(i, status='D', interface='backhaul', bandwidth=BANDWIDTH, flow='VoIP')
	for j in i.childs:
		i.connect(j, status='D', interface='access', bandwidth=BANDWIDTH, flow='VoIP')

# calc pre-inter-arrival-time of packets (encapsulate)
simulation_time = 1000
UE_lambda = [i.lambd for i in users]
interArrivalPkt = { i:[] for i in range(simulation_time)}

# for i in range(len(users)):
# 	for j in users[i].link['access']:
# 		pkt = {
# 			'device': users[i],
# 			'flow': j.flow,
# 			'delay_budget': config.traffic[j.flow]['delay_budget'],
# 			'bitrate': config.traffic[j.flow]['bitrate'],
# 			'arrival_time': random.expovariate(users[i].lambd)
# 		}

"""[summary] LBPS basic scheme

[description]
1. Aggr
2. Split
3. Merge
4. test by eNB
"""

# TestRN = copy.deepcopy(relays[0])
# result = LBPS(TestRN, 'aggr', show=True)

# TestRN = copy.deepcopy(relays[0])
# result = LBPS(TestRN, 'split', show=True)

# TestRN = copy.deepcopy(relays[0])
# result = LBPS(TestRN, 'merge', show=True)

# TestBS = copy.deepcopy(base_station)
# result = LBPS(TestBS, 'aggr', show=True)

# TestBS = copy.deepcopy(base_station)
# result = LBPS(TestBS, 'split', show=True)

# TestBS = copy.deepcopy(base_station)
# result = LBPS(TestBS, 'merge', show=True)

"""[summary] LBPS basic scheme with TDD

[description]
1. Aggr in TDD
2. Split in TDD
3. Merge in TDD

only RN will be assign TDD configuration so far

"""

# TDD_config = ONE_HOP_TDD_CONFIG[1]


# TestRN = copy.deepcopy(relays[0])
# TestRN.tdd_config = TDD_config
# result = LBPS(TestRN, 'aggr', TDD=True, show=True)

# TestRN = copy.deepcopy(relays[0])
# TestRN.tdd_config = TDD_config
# result = LBPS(TestRN, 'split', TDD=True, show=True)

# TestRN = copy.deepcopy(relays[0])
# TestRN.tdd_config = TDD_config
# result = LBPS(TestRN, 'merge', TDD=True, show=True)

"""[summary] proposed two-hop top-down LBPS in TDD

[description]
1. aggr-aggr
2. split-aggr
3. merge-aggr
"""

# TDD_config = TWO_HOP_TDD_CONFIG[0]

# TestBS = copy.deepcopy(base_station)
# TestBS.tdd_config = TDD_config
# result = LBPS(TestBS, 'aggr', backhaul='aggr', TDD=True, show=True)

# TestBS = copy.deepcopy(base_station)
# TestBS.tdd_config = TDD_config
# result = LBPS(TestBS, 'aggr', backhaul='split', TDD=True, show=True)

# TestBS = copy.deepcopy(base_station)
# TestBS.tdd_config = TDD_config
# result = LBPS(TestBS, 'aggr', backhaul='merge', TDD=True, show=True)