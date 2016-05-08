#!/usr/bin/python3

from __init__ import *
from pprint import pprint

# create device instance
base_station = eNB()
relays = [RN() for i in range(6)]
users = [UE() for i in range(240)]

# assign the relationship and CQI
base_station.childs = relays
for i in range(len(relays)):
	relays[i].childs = users[i*40:i*40+40]
	relays[i].parent = base_station
	relays[i].CQI = ['H']
	for j in range(i*40, i*40+40):
		users[j].parent = relays[i]
		users[j].CQI = ['M', 'H']

# build up the bearer from parent to child
for i in base_station.childs:
	for j in i.childs:
		i.connect(j, status='D', interface='access', bandwidth=BANDWIDTH, flow='VoIP')
	base_station.connect(i, status='D', interface='backhaul', bandwidth=BANDWIDTH, flow='VoIP')

# calc pre-inter-arrival-time of packets (encapsulate)
simulation_time = 10
timeline = { i:[] for i in range(simulation_time+1)}
UE_lambda = [i.lambd for i in users]

for i in range(len(users)):

	for bearer in users[i].link['access']:
		arrTimeByBearer = [0]

		# random process of getting inter-arrival-time by bearer
		while arrTimeByBearer[-1]<=simulation_time and users[i].lambd['access']:
			arrTimeByBearer.append(arrTimeByBearer[-1]+random.expovariate(users[i].lambd['access']))
		arrTimeByBearer[-1] > simulation_time and arrTimeByBearer.pop()
		arrTimeByBearer.pop(0)

		# assign pkt to real timeline
		for arrTime in range(len(arrTimeByBearer)):
			pkt = {
				'device': users[i],
				'flow': bearer.flow,
				'delay_budget': traffic[bearer.flow]['delay_budget'],
				'bitrate': traffic[bearer.flow]['bitrate'],
				'arrival_time': arrTimeByBearer[arrTime]
			}
			timeline[math.ceil(pkt['arrival_time'])].append(pkt)

for i in range(len(timeline)):
	timeline[i] = sorted(timeline[i], key=lambda x: x['arrival_time'])

# decide 2-hop TDD configuration (DL)(fixed)
candidate = TWO_HOP_TDD_CONFIG.copy()
radio_frame_pkt = [pkt for TTI in timeline for pkt in timeline[TTI] if TTI <= 10]
total_pktSize = sum([traffic[pkt['flow']]['pkt_size'] for pkt in radio_frame_pkt])

# backhaul and access filter for TDD configuration decision
n_b_subframe = math.ceil(total_pktSize / base_station.capacity)
candidate = {i: candidate[i] for i in candidate if candidate[i]['backhaul'].count('D') >= n_b_subframe}
n_a_subframe = [math.ceil(total_pktSize/len(base_station.childs)/i.capacity['access']) for i in base_station.childs]
candidate = {i: candidate[i] for i in candidate if candidate[i]['access'].count('D') >= max(n_a_subframe)}
base_station.tdd_config = random.choice(candidate) if candidate else None

if not base_station.tdd_config:
	msg_fail("no suitable TDD configuration")

msg_success("==========\tsimulation start\t==========")
discard_pkt = []
TTI = 1

# apply LBPS
# result = LBPS.aggr(base_station, duplex='FDD', show=True)
# result = LBPS.split(base_station, duplex='FDD', show=True)
# result = LBPS.merge(base_station, duplex='FDD', show=True)
result = LBPS.aggr_aggr(base_station, duplex='FDD', show=True)
pprint(result)

while TTI != simulation_time+1:

	# check the arrival pkt from internet
	if not timeline[TTI]:
		TTI += 1
		continue

	# discard timeout pkt and record
	for child in base_station.queue['backhaul']:
		for pkt in base_station.queue['backhaul'][child]:
			if TTI - pkt['arrival_time'] > pkt['delay_budget']:
				base_station.queue['backhaul'][child].remove(pkt)
				discard_pkt.append(pkt)

	# DeNB receive pkt from internet and classified
	for arrPkt in timeline[TTI]:
		base_station.queue['backhaul'][arrPkt['device'].parent.name].append(arrPkt)

	# check the sleep mode for each mode

	# transmission scheduling: 2-hop FIFO


	TTI += 1

msg_success("==========\tsimulation end\t\t==========")
