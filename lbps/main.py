#!/usr/bin/python3

from __init__ import *
from pprint import pprint

NUMBER_OF_RN = 6
NUMBER_OF_UE = 240
ITERATE_TIMES = 10
SIMULATION_TIME = 1000
PERFORMANCE = {'LAMBDA':[], 'TDD_CONFIG':[], 'RN-PSE':[], 'UE-PSE':[], 'DELAY':[]}

# create device instance
base_station = eNB()
relays = [RN() for i in range(NUMBER_OF_RN)]
users = [UE() for i in range(NUMBER_OF_UE)]

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

# loop for different data-rate
for i in range(ITERATE_TIMES):

	# dynamically adjust data rate and clear the queue history
	for rn in base_station.childs:
		for ue in rn.childs:
			rn.connect(ue, status='D', interface='access', bandwidth=BANDWIDTH, flow='VoIP')
	base_station.clearQueue()

	# calc pre-inter-arrival-time of packets (encapsulate)
	timeline = { i:[] for i in range(SIMULATION_TIME+1)}
	UE_lambda = [i.lambd for i in users]

	# assign pre-calc pkt arrival to timeline
	for i in range(len(users)):

		for bearer in users[i].link['access']:
			arrTimeByBearer = [0]

			# random process of getting inter-arrival-time by bearer
			while arrTimeByBearer[-1]<=SIMULATION_TIME and users[i].lambd['access']:
				arrTimeByBearer.append(arrTimeByBearer[-1]+random.expovariate(users[i].lambd['access']))
			arrTimeByBearer[-1] > SIMULATION_TIME and arrTimeByBearer.pop()
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
	max_b_subframe = max([candidate[i]['backhaul'].count('D') for i in candidate])
	max_a_subframe = max([candidate[i]['access'].count('D') for i in candidate])
	radio_frame_pkt = [pkt for TTI in timeline for pkt in timeline[TTI] if TTI <= 10]
	total_pktSize = sum([traffic[pkt['flow']]['pkt_size'] for pkt in radio_frame_pkt])

	# backhaul and access filter for TDD configuration decision
	n_b_subframe = math.ceil(total_pktSize / base_station.capacity)
	n_b_subframe = n_b_subframe if n_b_subframe <= max_b_subframe else max_b_subframe
	n_a_subframe = max([math.ceil(total_pktSize/len(base_station.childs)/i.capacity['access']) for i in base_station.childs])
	n_a_subframe = n_a_subframe if n_a_subframe <= max_a_subframe else max_a_subframe

	candidate = {i: candidate[i] for i in candidate if candidate[i]['backhaul'].count('D') >= n_b_subframe}
	candidate = {i: candidate[i] for i in candidate if candidate[i]['access'].count('D') >= n_a_subframe} \
				if len(candidate) > 1 else candidate

	b_sort = sorted(candidate, key=lambda x: candidate[x]['backhaul'].count('D'))
	b_sort = candidate[b_sort[0]]['backhaul'].count('D')
	candidate = {i: candidate[i] for i in candidate if candidate[i]['backhaul'].count('D') == b_sort}
	a_sort = sorted(candidate, key=lambda x: candidate[x]['access'].count('D'))
	a_sort = candidate[a_sort[0]]['access'].count('D')
	candidate = {i: candidate[i] for i in candidate if candidate[i]['access'].count('D') == a_sort}

	candidate_key = random.choice(list(candidate.keys()))
	base_station.tdd_config = candidate[candidate_key] if candidate else None

	if not base_station.tdd_config:
		msg_fail("no suitable TDD configuration")

	msg_success("==========\tsimulation start\t==========")
	performance = {ue.name:{'PSE':0, 'delay':0} for rn in base_station.childs for ue in rn.childs}
	performance.update({rn.name:{'PSE':0} for rn in base_station.childs})
	isSleep = {rn.name:False for rn in base_station.childs}
	isBLoading = {rn.name:False for rn in base_station.childs}
	isALoading = {rn.name:False for rn in base_station.childs}
	TTI = 1

	# apply LBPS
	# result = LBPS.aggr(base_station, duplex='FDD', show=True)
	# result = LBPS.split(base_station, duplex='FDD', show=True)
	# result = LBPS.merge(base_station, duplex='FDD', show=True)
	result = LBPS.aggr_aggr(base_station, duplex='TDD', show=True) \
			if LBPS.getLoad(base_station, 'TDD') <= 1 else None
	# pprint(result)

	while TTI != SIMULATION_TIME+1:

		# check the arrival pkt from internet
		if timeline[TTI]:
			for arrPkt in timeline[TTI]:
				base_station.queue['backhaul'][arrPkt['device'].parent.name].append(arrPkt)

		# check each RN operation by sleep mode or backhaul/access transmission
		for rn in base_station.childs:
			r_pos = (TTI-1)%len(result)+1 if result else None
			available_cap = 0
			interface = None

			# device the sleep mode
			# awake:
			# 	1. load > 1
			# 	2. lbps waking subframe
			# 	3. pre-subframe cannot serve all pkt int the queue
			if not r_pos:
				# print("TTI " + str(TTI) +": load > 1", end='\t')
				isSleep[rn.name] = False
			elif r_pos and result[r_pos] and rn in result[r_pos]:
				# print("TTI " + str(TTI) +": lbps waking subframe", end='\t')
				isSleep[rn.name] = False
			elif isBLoading[rn.name] or isALoading[rn.name]:
				# print("TTI " + str(TTI) +": pre-subframe cannot serve all pkt int the queue", end='\t')
				isSleep[rn.name] = False
			else:
				# print("TTI " + str(TTI) +": sleep", end='\t')
				isSleep[rn.name] = True

			# check if RN awake
			if not isSleep[rn.name]:

				if not r_pos or (result[r_pos] and rn not in result[r_pos]):
					interface = 'backhaul' if base_station.tdd_config[(TTI-1)%10] == 'D' else 'access'

				else:
					interface = 'backhaul' if result[r_pos] and base_station in result[r_pos] else 'access'

				available_cap = rn.capacity[interface]
				check_queue = base_station.queue['backhaul'][rn.name] \
					if interface == 'backhaul' else rn.queue['backhaul']

				if interface == 'backhaul':
					for ue in rn.childs:
						performance[ue.name]['PSE'] += 1/SIMULATION_TIME

				# calc avaliable pkt for transmission
				for pkt in check_queue:

					# still have data buffer in queue
					if available_cap < traffic[pkt['flow']]['pkt_size']:
						if interface == 'backhaul':
							isBLoading[rn.name] = True
						elif interface == 'access':
							isALoading [rn.name] = True
						break

					if interface == 'backhaul':
						rn.queue[interface].append(pkt)
						base_station.queue['backhaul'][rn.name].remove(pkt)
						isBLoading[rn.name] = False

					elif interface == 'access':
						rn.queue['access'][pkt['device'].name].append(pkt)
						performance[pkt['device'].name]['delay'] += TTI-math.ceil(pkt['arrival_time'])
						rn.queue['backhaul'].remove(pkt)
						isALoading[rn.name] = False

					available_cap -= traffic[pkt['flow']]['pkt_size']

			else:
				performance[rn.name]['PSE'] += 1/SIMULATION_TIME
				for ue in rn.childs:
					performance[ue.name]['PSE'] += 1/SIMULATION_TIME

		TTI += 1

	msg_success("==========\tsimulation end\t\t==========")

	# performance output
	ue_name = [ue.name for rn in base_station.childs for ue in rn.childs]
	deliver_pkt = [len(rn.queue['access'][ue.name]) for rn in base_station.childs for ue in rn.childs]

	PERFORMANCE['LAMBDA'].append(base_station.lambd['backhaul'])
	PERFORMANCE['TDD_CONFIG'].append(base_station.tdd_config)
	PERFORMANCE['UE-PSE'].append(round(sum([performance[ue]['PSE'] for ue in ue_name])/NUMBER_OF_UE, 2))
	PERFORMANCE['RN-PSE'].append(round(sum([performance[rn.name]['PSE'] for rn in base_station.childs])/NUMBER_OF_RN, 2))
	PERFORMANCE['DELAY'].append(round(sum([performance[ue]['delay'] for ue in ue_name])/sum(deliver_pkt), 2))

pprint(PERFORMANCE)
export_csv(PERFORMANCE)
