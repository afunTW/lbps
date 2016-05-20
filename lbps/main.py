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
	loading = {
		'backhaul': {rn.name:False for rn in base_station.childs},
		'access': {rn.name:False for rn in base_station.childs}
	}

	# apply LBPS
	lbps = LBPS.aggr_aggr(base_station, SIMULATION_TIME, duplex='TDD')

	for TTI in range(SIMULATION_TIME):

		# check the arrival pkt from internet
		if timeline[TTI]:
			for arrPkt in timeline[TTI]:
				base_station.queue['backhaul'][arrPkt['device'].parent.name].append(arrPkt)

		for rn in base_station.childs:
			real_timeline_collision = False
			interface = None

			# case: subframe 'S' or 'U'
			if rn.tdd_config[TTI%10] != 'D':
				# performance[rn.name]['PSE'] += 1/SIMULATION_TIME
				# for ue in rn.childs:
				# 	performance[ue.name]['PSE'] += 1/SIMULATION_TIME
				continue

			# lbps case
			if rn in lbps['backhaul'][TTI] and rn in lbps['access'][TTI]:
				interface = 'backhaul'
				real_timeline_collision = True
			elif rn in lbps['backhaul'][TTI]:
				interface = 'backhaul'
			elif rn in lbps['access'][TTI]:
				interface = 'access'

			# traffic stuck
			if loading['backhaul'][rn.name] and base_station.tdd_config[TTI%10]:
				interface = 'backhaul'
			elif loading['access'][rn.name] and rn.tdd_config[TTI%10]:
				interface = 'access'

			# backhaul transmission
			if interface == 'backhaul':
				if not base_station.queue[interface][rn.name] and real_timeline_collision:
					interface = 'access'
				else:
					available_cap = rn.capacity[interface]
					for pkt in base_station.queue[interface][rn.name]:
						if available_cap >= pkt['size']:
							rn.queue[interface].append(pkt)
							base_station.queue[interface][rn.name].remove(pkt)
							available_cap -= pkt['size']
						else:
							loading[interface][rn.name] = True
							break
					for ue in rn.childs:
						performance[ue.name]['PSE'] += 1/SIMULATION_TIME
					if not base_station.queue[interface][rn.name]:
						loading[interface][rn.name] = False

			# access transmission
			if interface == 'access':
				available_cap = rn.capacity[interface]
				for pkt in rn.queue['backhaul']:
					if available_cap >= pkt['size']:
						rn.queue['access'][pkt['device'].name].append(pkt)
						rn.queue['backhaul'].remove(pkt)
						performance[pkt['device'].name]['delay'] += TTI-pkt['arrival_time']
						available_cap -= pkt['size']
					else:
						loading[interface][rn.name] = True
						break
				if not rn.queue['backhaul']:
					loading[interface][rn.name] = False

			# sleep
			if not interface:
				performance[rn.name]['PSE'] += 1/SIMULATION_TIME
				for ue in rn.childs:
					performance[ue.name]['PSE'] += 1/SIMULATION_TIME

	msg_success("==========\tsimulation end\t\t==========")

	# performance output
	ue_name = [ue.name for rn in base_station.childs for ue in rn.childs]
	deliver_pkt = [len(rn.queue['access'][ue.name]) for rn in base_station.childs for ue in rn.childs]

	PERFORMANCE['LAMBDA'].append(base_station.lambd['backhaul'])
	PERFORMANCE['CAPACITY'].append(round(base_station.capacity/1000, 2))
	PERFORMANCE['V_CAPACITY'].append(round(base_station.virtualCapacity/1000, 2))
	PERFORMANCE['TDD_CONFIG'].append(base_station.tdd_config)
	PERFORMANCE['UE-PSE'].append(round(sum([performance[ue]['PSE'] for ue in ue_name])/NUMBER_OF_UE, 2))
	PERFORMANCE['RN-PSE'].append(round(sum([performance[rn.name]['PSE'] for rn in base_station.childs])/NUMBER_OF_RN, 2))
	PERFORMANCE['DELAY'].append(round(sum([performance[ue]['delay'] for ue in ue_name])/sum(deliver_pkt), 2))

pprint(PERFORMANCE)
export_csv(PERFORMANCE)
