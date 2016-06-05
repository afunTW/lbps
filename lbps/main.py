#!/usr/bin/python3

from __init__ import *
from pprint import pprint

NUMBER_OF_RN = 6
NUMBER_OF_UE = 240

def update_nested_dict(d1, d2):
	for k,v in d1.items():
		if type(v) is list:
			v.extend(d2[k])
		elif type(v) is dict:
			update_nested_dict(v, d2[k])

def transmission_scheduling(base_station, simulation_time=1000):
	prefix = "transmissing_scheduling failed"
	try:
		round_para = len(str(int(simulation_time/10)))

		# apply LBPS
		scheduling = {
			'TD-aggr': LBPS.top_down,
			'TD-split': LBPS.top_down,
			'TD-merge': LBPS.top_down,
			'BU-aggr': LBPS.bottom_up,
			'BU-split': LBPS.bottom_up,
			'BU-merge': LBPS.bottom_up
		}

		for (PS, lbps) in scheduling.items():

			msg_success("==========\t\t%s simulation with lambda %g Mbps start\t\t=========="%\
					(PS, base_station.lambd['backhaul']))
			lbps = lbps(PS[3:], base_station, simulation_time)

			base_station.clearQueue()
			performance = {
				ue.name:{
					'sleep':0,
					'delay':0,
					'force-awake':False
				} for rn in base_station.childs for ue in rn.childs}
			performance.update({
				rn.name:{
					'sleep':0,
					'awake':{'backhaul':0, 'access':0},
					'force-awake':{'backhaul':0, 'access':0}
				} for rn in base_station.childs})
			loading = {
				'backhaul': {rn.name:False for rn in base_station.childs},
				'access': {rn.name:False for rn in base_station.childs}
			}

			for TTI in range(simulation_time):

				# check the arrival pkt from internet
				if timeline[TTI]:
					for arrPkt in timeline[TTI]:
						base_station.queue['backhaul'][arrPkt['device'].parent.name].append(arrPkt)

				for rn in base_station.childs:
					real_timeline_collision = False
					interface = None

					# case: subframe 'S' or 'U'
					if rn.tdd_config[TTI%10] != 'D':
						performance[rn.name]['sleep'] += 1
						for ue in rn.childs:
							performance[ue.name]['sleep'] += 1
						continue

					# lbps case
					if rn in lbps['backhaul'][TTI]:
						interface = 'backhaul'
					elif rn in lbps['access'][TTI]:
						interface = 'access'

					# traffic stuck
					if base_station.tdd_config[TTI%10] and loading['backhaul'][rn.name]:
						interface = 'backhaul'
					elif loading['access'][rn.name]:
						interface = 'access'

					# backhaul transmission
					if interface == 'backhaul':
						if not base_station.queue[interface][rn.name] and rn in lbps['access'][TTI]:
							interface = 'access'
						else:
							performance[rn.name]['awake'][interface] += 1
							available_cap = rn.capacity[interface]
							unavailable_index = len(base_station.queue[interface][rn.name])

							for i in range(len(base_station.queue[interface][rn.name])):
								pkt = base_station.queue[interface][rn.name][i]
								if available_cap >= pkt['size']:
									rn.queue[interface].append(pkt)
									available_cap -= pkt['size']
								else:
									unavailable_index = i
									break

							del base_station.queue[interface][rn.name][:unavailable_index]
							loading[interface][rn.name] = True if base_station.queue[interface][rn.name] else False
							performance[rn.name]['force-awake'][interface] += 1 if loading[interface][rn.name] else 0

							for ue in rn.childs:
								performance[ue.name]['sleep'] += 1

					# access transmission
					if interface == 'access':
						performance[rn.name]['awake'][interface] += 1
						available_cap = rn.capacity[interface]
						success_pkt = []

						for i in range(len(rn.queue['backhaul'])):
							pkt = rn.queue['backhaul'][i]
							if available_cap >= pkt['size'] and pkt['device'] in lbps[interface][TTI]\
								or performance[pkt['device'].name]['force-awake']:
								rn.queue[interface][pkt['device'].name].append(pkt)
								performance[pkt['device'].name]['delay'] += TTI-pkt['arrival_time']
								success_pkt.append(pkt)
								available_cap -= pkt['size']

						rn.queue['backhaul'] = [i for i in rn.queue['backhaul'] if i not in success_pkt]

						for ue in rn.childs:
							performance[ue.name]['force-awake'] = False

						force_awake_by_ue = False
						for pkt in rn.queue['backhaul']:
							if pkt['device'] in lbps[interface][TTI]:
								performance[pkt['device'].name]['force-awake'] = True
								force_awake_by_ue = True

						loading[interface][rn.name] = True if rn.queue['backhaul'] and force_awake_by_ue else False
						performance[rn.name]['force-awake']['access'] += 1 if loading[interface][rn.name] else 0

						for ue in rn.childs:
							if ue not in lbps[interface][TTI] and not performance[ue.name]['force-awake']:
								performance[ue.name]['sleep'] += 1

					# sleep
					if not interface:
						performance[rn.name]['sleep'] += 1
						for ue in rn.childs:
							performance[ue.name]['sleep'] += 1

			# test
			print(base_station.name, end='\t')
			msg_execute("CQI= %d" % base_station.CQI)
			for i in base_station.childs:
				print(i.name, end='\t')
				msg_execute("CQI= %d" % i.CQI, end='\t\t')
				msg_execute("sleep: %d times" % performance[i.name]['sleep'], end='\t\t')
				msg_warning("force awake in backhaul: %d times" % performance[i.name]['force-awake']['backhaul'], end='\t')
				msg_warning("force awake in access: %d times" % performance[i.name]['force-awake']['access'])

			# performance output
			ue_name = [ue.name for rn in base_station.childs for ue in rn.childs]
			deliver_pkt = [len(rn.queue['access'][ue.name]) for rn in base_station.childs for ue in rn.childs]
			total_ue_pse = sum([performance[ue]['sleep'] for ue in ue_name])/simulation_time
			total_rn_pse = sum([performance[rn.name]['sleep'] for rn in base_station.childs])/simulation_time
			total_delay = sum([performance[ue]['delay'] for ue in ue_name])

			ue_pse = round(total_ue_pse/NUMBER_OF_UE, round_para)
			rn_pse = round(total_rn_pse/NUMBER_OF_RN, round_para)
			avg_delay = round(total_delay/sum(deliver_pkt), round_para)

			PERFORMANCE['UE-PSE'][PS].append(ue_pse)
			PERFORMANCE['RN-PSE'][PS].append(rn_pse)
			PERFORMANCE['DELAY'][PS].append(avg_delay)
			PERFORMANCE['PSE-FAIRNESS'][PS].append(round(\
				total_ue_pse**2/\
				(NUMBER_OF_UE*sum([(performance[ue]['sleep']/simulation_time)**2 for ue in ue_name]))\
				,round_para
			))
			PERFORMANCE['DELAY-FAIRNESS'][PS].append(round(\
				total_delay**2/\
				(NUMBER_OF_UE*sum([performance[ue]['delay']**2 for ue in ue_name]))\
				, round_para
			))

			msg_success("==========\t\t%s simulation with lambda %g Mbps end\t\t=========="%\
					(PS, base_station.lambd['backhaul']))

		PERFORMANCE['LAMBDA'].append(base_station.lambd['backhaul'])
		PERFORMANCE['LOAD'].append(round(LBPS.getLoad(base_station, 'TDD'), round_para))

		return PERFORMANCE

	except Exception as e:
		msg_fail(str(e), pre=prefix)

if __name__ == '__main__':

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

	# case: equal load
	iterate_times = 10
	simulation_time = 10000
	PERFORMANCE = {
		'LAMBDA':[],
		'LOAD':[],
		'RN-PSE':{'TD-aggr':[],'TD-split':[],'TD-merge':[],'BU-aggr':[],'BU-split':[],'BU-merge':[]},
		'UE-PSE':{'TD-aggr':[],'TD-split':[],'TD-merge':[],'BU-aggr':[],'BU-split':[],'BU-merge':[]},
		'DELAY':{'TD-aggr':[],'TD-split':[],'TD-merge':[],'BU-aggr':[],'BU-split':[],'BU-merge':[]},
		'PSE-FAIRNESS':{'TD-aggr':[],'TD-split':[],'TD-merge':[],'BU-aggr':[],'BU-split':[],'BU-merge':[]},
		'DELAY-FAIRNESS':{'TD-aggr':[],'TD-split':[],'TD-merge':[],'BU-aggr':[],'BU-split':[],'BU-merge':[]}
	}

	for i in range(iterate_times):

		# increase lambda
		for rn in base_station.childs:
			for ue in rn.childs:
				rn.connect(ue, status='D', interface='access', bandwidth=BANDWIDTH, flow='VoIP')

		timeline = base_station.simulate_timeline(simulation_time)
		base_station.choose_tdd_config(timeline, fixed=17)

		# test lbps performance in transmission scheduling
		performance = transmission_scheduling(base_station, simulation_time=simulation_time)
		update_nested_dict(PERFORMANCE, performance)

	pprint(PERFORMANCE, indent=2)
	export_csv(performance)