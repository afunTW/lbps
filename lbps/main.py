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

# build up the bearer from parent to child
for i in base_station.childs:
	base_station.connect(i, status='D', interface='backhaul', bandwidth=BANDWIDTH, flow='VoIP')
	for j in i.childs:
		i.connect(j, status='D', interface='access', bandwidth=BANDWIDTH, flow='VoIP')

# calc pre-inter-arrival-time of packets (encapsulate)
simulation_time = 1000
timeline = { i:[] for i in range(simulation_time+1)}
UE_lambda = [i.lambd for i in users]

for i in range(len(users)):

	for bearer in users[i].link['access']:
		arrTimeByBearer = [0]

		# random process of getting inter-arrival-time by bearer
		while arrTimeByBearer[-1]<=simulation_time:
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

msg_success("==========\tsimulation start\t==========")
discard_pkt = []
TTI = 1

while TTI != simulation_time+1:

	# check the arrival pkt from internet
	if not timeline[TTI]:
		TTI += 1
		continue

	# discard timeout pkt and record
	for pkt in base_station.queue['internet']:
		if TTI - pkt['arrival_time'] > pkt['delay_budget']:
			base_station.queue['internet'].remove(pkt)
			discard_pkt.append(pkt)

	base_station.queue['internet'] += timeline[TTI]

	TTI += 1

msg_success("==========\tsimulation end\t\t==========")