#!/usr/bin/python3

from __init__ import *
from pprint import pprint

NUMBER_OF_RN = 6
NUMBER_OF_UE = 240
ITERATE_TIMES = 1
SIMULATION_TIME = 1000
PERFORMANCE = {
	'LAMBDA':[],
	'LOAD':[],
	'RN-PSE':{
		'aggr-aggr':[],
		'split-aggr':[],
		'merge-aggr':[]
	},
	'UE-PSE':{
		'aggr-aggr':[],
		'split-aggr':[],
		'merge-aggr':[]
	},
	'DELAY':{
		'aggr-aggr':[],
		'split-aggr':[],
		'merge-aggr':[]
	},
	'PSE-FAIRNESS':{
		'aggr-aggr':[],
		'split-aggr':[],
		'merge-aggr':[]
	},
	'DELAY-FAIRNESS':{
		'aggr-aggr':[],
		'split-aggr':[],
		'merge-aggr':[]
	}
}

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

	timeline = base_station.simulate_timeline(SIMULATION_TIME)
	base_station.choose_tdd_config(timeline, fixed=17)

	# apply LBPS
	scheduling = {
		'aggr-aggr': LBPS.top_down('aggr', base_station, SIMULATION_TIME),
		'split-aggr': LBPS.top_down('split', base_station, SIMULATION_TIME),
		'merge-aggr': LBPS.top_down('merge', base_station, SIMULATION_TIME),
		'min-aggr': LBPS.min_aggr(base_station, SIMULATION_TIME)
	}

	for (PS, lbps) in scheduling.items():

		msg_success("==========\t\t%s simulation with lambda %g Mbps start\t\t=========="%\
				(PS, base_station.lambd['backhaul']))

		base_station.clearQueue()
		performance = {ue.name:{'PSE':0, 'delay':0} for rn in base_station.childs for ue in rn.childs}
		performance.update({rn.name:{'PSE':0} for rn in base_station.childs})
		loading = {
			'backhaul': {rn.name:False for rn in base_station.childs},
			'access': {rn.name:False for rn in base_station.childs}
		}


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
								# msg_warning("%s remain %d pkt in backhaul %d TTI" %\
								# 	(rn.name, len(base_station.queue[interface][rn.name]), TTI))
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
							# msg_warning("%s remain %d pkt in access %d TTI" %\
							# 		(rn.name, len(rn.queue['backhaul']), TTI))
							break
					if not rn.queue['backhaul']:
						loading[interface][rn.name] = False

				# sleep
				if not interface:
					performance[rn.name]['PSE'] += 1/SIMULATION_TIME
					for ue in rn.childs:
						performance[ue.name]['PSE'] += 1/SIMULATION_TIME

		# performance output
		ue_name = [ue.name for rn in base_station.childs for ue in rn.childs]
		deliver_pkt = [len(rn.queue['access'][ue.name]) for rn in base_station.childs for ue in rn.childs]
		total_ue_pse = sum([performance[ue]['PSE'] for ue in ue_name])
		total_rn_pse = sum([performance[rn.name]['PSE'] for rn in base_station.childs])
		total_delay = sum([performance[ue]['delay'] for ue in ue_name])

		# test
		for i in base_station.childs:
			print(i.name, end='\t')
			msg_warning("CQI= %g" % i.CQI, end='\t\t')
			msg_warning("delay= %g bits" % sum([performance[ue.name]['delay'] for ue in i.childs]))

		ue_pse = round(total_ue_pse/NUMBER_OF_UE, 2)
		rn_pse = round(total_rn_pse/NUMBER_OF_RN, 2)
		avg_delay = round(total_delay/sum(deliver_pkt), 2)

		PERFORMANCE['UE-PSE'][PS].append(ue_pse)
		PERFORMANCE['RN-PSE'][PS].append(rn_pse)
		PERFORMANCE['DELAY'][PS].append(avg_delay)
		PERFORMANCE['PSE-FAIRNESS'][PS].append(round(\
			total_ue_pse**2/\
			(NUMBER_OF_UE*sum([performance[ue]['PSE']**2 for ue in ue_name]))\
			,2
		))
		PERFORMANCE['DELAY-FAIRNESS'][PS].append(round(\
			total_delay**2/\
			(NUMBER_OF_UE*sum([performance[ue]['delay']**2 for ue in ue_name]))\
			, 2
		))

		msg_success("==========\t\t%s simulation with lambda %g Mbps end\t\t=========="%\
				(PS, base_station.lambd['backhaul']))

	PERFORMANCE['LAMBDA'].append(base_station.lambd['backhaul'])
	PERFORMANCE['LOAD'].append(round(LBPS.getLoad(base_station, 'TDD'), 2))

pprint(PERFORMANCE, indent=2)
export_csv(PERFORMANCE)
