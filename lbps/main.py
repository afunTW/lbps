#!/usr/bin/python3

from __init__ import *
from pprint import pprint

NUMBER_OF_RN = 6
NUMBER_OF_UE = 240
ITERATE_TIMES = 10
SIMULATION_TIME = 1000
PERFORMANCE = {'LAMBDA':[], 'CAPACITY':[], 'V_CAPACITY':[], 'TDD_CONFIG':[], 'RN-PSE':[], 'UE-PSE':[], 'DELAY':[]}

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
	timeline = base_station.simulate_timeline(SIMULATION_TIME)
	base_station.choose_tdd_config(timeline)

	msg_success("==========\tsimulation start\t==========")
	performance = {ue.name:{'PSE':0, 'delay':0} for rn in base_station.childs for ue in rn.childs}
	performance.update({rn.name:{'PSE':0} for rn in base_station.childs})
	sleep = {rn.name:False for rn in base_station.childs}
	b_loading = {rn.name:False for rn in base_station.childs}
	a_loading = {rn.name:False for rn in base_station.childs}

	# apply LBPS
	lbps = LBPS.aggr_aggr(base_station, SIMULATION_TIME, duplex='TDD')

	for TTI in range(SIMULATION_TIME):

		# check the arrival pkt from internet
		if timeline[TTI]:
			for arrPkt in timeline[TTI]:
				base_station.queue['backhaul'][arrPkt['device'].parent.name].append(arrPkt)

		for rn in base_station.childs:

			# case: subframe 'S' or 'U'
			if rn.tdd_config[TTI%10] != 'D':
				continue

			# rn wake up in the case of lbps or heavy load
			if rn in lbps['backhaul'][TTI]
				or rn in lbps['access'][TTI]
				or b_loading[rn.name] or a_loading[rn.name]:
				interface = None
				available_cap = 0


			# # device the sleep mode
			# # awake:
			# # 	1. lbps waking subframe
			# # 	2. pre-subframe cannot serve all pkt int the queue
			# if not r_pos:
			# 	# print("TTI " + str(TTI) +": load > 1", end='\t')
			# 	isSleep[rn.name] = False
			# elif r_pos and result[r_pos] and rn in result[r_pos]:
			# 	# print("TTI " + str(TTI) +": lbps waking subframe", end='\t')
			# 	isSleep[rn.name] = False
			# elif isBLoading[rn.name] or isALoading[rn.name]:
			# 	# print("TTI " + str(TTI) +": pre-subframe cannot serve all pkt int the queue", end='\t')
			# 	isSleep[rn.name] = False
			# else:
			# 	# print("TTI " + str(TTI) +": sleep", end='\t')
			# 	isSleep[rn.name] = True

			# # check if RN awake
			# if not isSleep[rn.name]:

			# 	if not r_pos or (result[r_pos] and rn not in result[r_pos]):
			# 		interface = 'backhaul' if base_station.tdd_config[(TTI-1)%10] == 'D' else 'access'

			# 	else:
			# 		interface = 'backhaul' if result[r_pos] and base_station in result[r_pos] else 'access'

			# 	available_cap = rn.capacity[interface]
			# 	check_queue = base_station.queue['backhaul'][rn.name] \
			# 		if interface == 'backhaul' else rn.queue['backhaul']

			# 	if interface == 'backhaul':
			# 		for ue in rn.childs:
			# 			performance[ue.name]['PSE'] += 1/SIMULATION_TIME

			# 	# calc avaliable pkt for transmission
			# 	for pkt in check_queue:

			# 		# still have data buffer in queue
			# 		if available_cap < traffic[pkt['flow']]['pkt_size']:
			# 			if interface == 'backhaul':
			# 				isBLoading[rn.name] = True
			# 			elif interface == 'access':
			# 				isALoading [rn.name] = True
			# 			break

			# 		if interface == 'backhaul':
			# 			rn.queue[interface].append(pkt)
			# 			base_station.queue['backhaul'][rn.name].remove(pkt)
			# 			isBLoading[rn.name] = False

			# 		elif interface == 'access':
			# 			rn.queue['access'][pkt['device'].name].append(pkt)
			# 			performance[pkt['device'].name]['delay'] += TTI-math.ceil(pkt['arrival_time'])
			# 			rn.queue['backhaul'].remove(pkt)
			# 			isALoading[rn.name] = False

			# 		available_cap -= traffic[pkt['flow']]['pkt_size']

			# else:
			# 	performance[rn.name]['PSE'] += 1/SIMULATION_TIME
			# 	for ue in rn.childs:
			# 		performance[ue.name]['PSE'] += 1/SIMULATION_TIME

	msg_success("==========\tsimulation end\t\t==========")

	# performance output
	# ue_name = [ue.name for rn in base_station.childs for ue in rn.childs]
	# deliver_pkt = [len(rn.queue['access'][ue.name]) for rn in base_station.childs for ue in rn.childs]

	# PERFORMANCE['LAMBDA'].append(base_station.lambd['backhaul'])
	# PERFORMANCE['CAPACITY'].append(round(base_station.capacity/1000, 2))
	# PERFORMANCE['V_CAPACITY'].append(round(base_station.virtualCapacity/1000, 2))
	# PERFORMANCE['TDD_CONFIG'].append(base_station.tdd_config)
	# PERFORMANCE['UE-PSE'].append(round(sum([performance[ue]['PSE'] for ue in ue_name])/NUMBER_OF_UE, 2))
	# PERFORMANCE['RN-PSE'].append(round(sum([performance[rn.name]['PSE'] for rn in base_station.childs])/NUMBER_OF_RN, 2))
	# PERFORMANCE['DELAY'].append(round(sum([performance[ue]['delay'] for ue in ue_name])/sum(deliver_pkt), 2))

pprint(PERFORMANCE)
# export_csv(PERFORMANCE)
