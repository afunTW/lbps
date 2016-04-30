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

TDD_config = ONE_HOP_TDD_CONFIG[1]

TestBS = copy.deepcopy(base_station)
TestBS.tdd_config = TDD_config
result = LBPS(TestBS, 'aggr', backhaul='aggr', TDD=True, show=True)

# TestBS = copy.deepcopy(base_station)
# TestBS.tdd_config = TDD_config
# result = LBPS(TestBS, 'aggr', backhaul='split', TDD=True, show=True)

# TestBS = copy.deepcopy(base_station)
# TestBS.tdd_config = TDD_config
# result = LBPS(TestBS, 'aggr', backhaul='merge', TDD=True, show=True)