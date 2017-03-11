import random
import copy
import re
from math import log, floor, ceil
from tdd import continuous_mapping as M2
from tdd import two_hop_mapping as m_2hop
from device import UE, RN, eNB

from poisson import getDataTH, LengthAwkSlpCyl, DataAcc
from config import *
from viewer import *
from pprint import pprint

"""[summary] internal function

[description] abstract level of lbps
"""

def getLoad(device, duplex="FDD"):

	try:
		interface = 'backhaul' if isinstance(device, eNB) else 'access'
		capacity = device.capacity if duplex == 'FDD' else device.virtualCapacity
		capacity = capacity[interface] if type(capacity) is dict else capacity
		return device.lambd[interface]*getAvgPktSize(device)/capacity

	except Exception as e:
		msg_fail(str(e), pre="%s::getLoad\t\t" % device.name)

def getAvgPktSize(device):
	interface = 'backhaul' if isinstance(device, eNB) else 'access'
	total_pkt = [bearer.flow for bearer in device.link[interface]]
	total_pkt = [traffic[i]['pkt_size'] for i in total_pkt]
	return sum(total_pkt)/len(total_pkt)

def schedulability(check_list):

	result = True if sum([1/cycle for cycle in check_list]) <= 1 else False;
	# result and msg_success("Check schedulability:\tTrue")
	# not result and msg_warning("Check schedulability:\tFalse")

	return result

def non_degraded(G, interface, DATA_TH):

	if len(G) is 1:
		return G

	source_G = G.pop(0)
	result = False

	for i in G:
		new_K = LengthAwkSlpCyl(source_G['lambda']+i['lambda'], DATA_TH)
		new_K = 2**floor(log(new_K, 2))
		if new_K == i['K']:
			result = True
			i['device'] += source_G['device']
			i['lambda'] += source_G['lambda']
			break

	not result and G.append(source_G)
	G.sort(key=lambda x: x['K'], reverse=True)

	return G

def two_hop_realtimeline(mapping_pattern, t, b, a):
	k = len(a)

	# extend and align timeline
	b_lbps_result = b*ceil(t/len(b))
	b_lbps_result = b_lbps_result[:t]
	a_lbps_result = a*ceil(t/len(a))
	a_lbps_result = a_lbps_result[:t]
	timeline = {'backhaul':[[] for i in range(t)], 'access':[[] for i in range(t)]}
	vt_mapping = {'backhaul':[], 'access':[]}

	for i in range(ceil(t/10)):
		vt_mapping['backhaul'] += [[i*10+v for v in su] for su in mapping_pattern['backhaul']]
		vt_mapping['access'] += [{
			'identity':su['identity'],
			'TTI': [i*10+v for v in su['r_TTI']]} for su in mapping_pattern['access']]

	# backhaul mapping
	for i in range(t):
		for rsb in vt_mapping['backhaul'][i]:
			timeline['backhaul'][rsb] += b_lbps_result[i]

	# access mapping
	for i in range(0, t-k, k):
		tmp_map = {'access':[], 'mixed':[], 'backhaul':[]}
		for j in vt_mapping['access'][i:i+k]:
			tmp_map[j['identity']].append(j)

		for vt in a_lbps_result[i:i+k]:
			if not vt:
				continue

			identity = 'backhaul' if tmp_map['backhaul'] else None
			identity = 'mixed' if tmp_map['mixed'] else identity
			identity = 'access' if tmp_map['access'] else identity

			for rsb in tmp_map[identity][0]['TTI']:
				timeline['access'][rsb] += vt

			tmp_map[identity].pop(0)

	for i in range(len(timeline['backhaul'])):
		timeline['backhaul'][i] = list(set(timeline['backhaul'][i]))
		timeline['access'][i] = list(set(timeline['access'][i]))

	return timeline

def schedule_failed(device):
	Bh_result = [rn for rn in device.childs]
	Bh_result.append(device)
	Ai_result = [ue for rn in device.childs for ue in rn.childs]
	Ai_result += [rn for rn in device.childs]
	return [Bh_result], [Ai_result]

def mincycle_shrinking(rn_status, Bh_K):
	for rn in rn_status.keys():
		rate = rn.virtualCapacity/rn.parent.virtualCapacity
		if rn_status[rn]['Ai_K'] > Bh_K:
			pkt_size = getAvgPktSize(rn)
			accumulate_pkt = DataAcc(rn.lambd['access'], Bh_K)
			rn_status[rn].update({'Ai_K':Bh_K})
			accumulate_pkt and\
			rn_status[rn].update({'Bh_count':ceil(accumulate_pkt*pkt_size*rate)})

def mincycle_schedulability(rn_status, Bh_K):
	Ai_check = []
	for v in rn_status.values():
		check = True if v['Ai_count']+v['Bh_count']<=Bh_K else False
		Ai_check.append(check)

	return sum([v['Bh_count'] for v in rn_status.values()])<=Bh_K, all(Ai_check)

def get_sleep_cycle(device, b_lbps_result, a_lbps_result):
	return {
		'RN':{rn.name:\
			[len(b_lbps_result)/sum([1 for TTI in b_lbps_result if rn in TTI])]\
			for rn in device.childs},
		'UE':{ue.name:\
			[len(a_lbps_result)/sum([1 for TTI in a_lbps_result if ue in TTI ])]\
			for rn in device.childs for ue in rn.childs}
	}

"""[summary] original lbps algorithm

[description] for one-hop in FDD
"""

def aggr(device, duplex='FDD'):

	prefix = "lbps::aggr::%s \t" % device.name

	try:
		# duplex will only affect the capacity, not related to mapping
		if duplex is not 'FDD' and duplex is not 'TDD':
			return

		if not isinstance(device, eNB) and not isinstance(device, RN):
			return

		interface = 'backhaul' if isinstance(device, eNB) else 'access'
		capacity = device.capacity if duplex == 'FDD' else device.virtualCapacity
		capacity = capacity[interface] if type(capacity) is dict else capacity
		pkt_size = getAvgPktSize(device)
		DATA_TH = int(getDataTH(capacity, pkt_size))
		msg_execute("load= %g\t" % getLoad(device, duplex), pre=prefix)

		# aggr process
		sleep_cycle_length = LengthAwkSlpCyl(device.lambd[interface], DATA_TH)
		msg_execute("sleepCycle = %d" % sleep_cycle_length ,pre=prefix)

		result = [[] for i in range(sleep_cycle_length)]
		result[0] = [i for i in device.childs]
		result[0].append(device)
		result[0] = sorted(result[0], key=lambda d: d.name)

		return result

	except Exception as e:
		msg_fail(str(e), pre=prefix)
		return

def split(device, duplex='FDD', boundary_group=None):

	prefix = "lbps::split::%s\t" % device.name

	try:
		# duplex will only affect the capacity, not related to mapping
		if duplex is not 'FDD' and duplex is not 'TDD':
			return

		if not isinstance(device, eNB) and not isinstance(device, RN):
			return

		interface = 'backhaul' if isinstance(device, eNB) else 'access'
		capacity = device.capacity if duplex == 'FDD' else device.virtualCapacity
		capacity = capacity[interface] if type(capacity) is dict else capacity
		pkt_size = getAvgPktSize(device)
		DATA_TH = int(getDataTH(capacity, pkt_size))
		msg_execute("load= %g\t" % getLoad(device, duplex), pre=prefix)
		sleep_cycle_length = LengthAwkSlpCyl(device.lambd[interface], DATA_TH)

		groups = {
			0: {
				'device': [ch for ch in device.childs],
				'lambda': device.lambd[interface],
				'K': sleep_cycle_length
			}
		}

		if not boundary_group or boundary_group > len(device.childs):
			boundary_group = len(device.childs)

		# Split process
		while len(groups) < sleep_cycle_length:
			groups = {
				i:{
					'device': [],
					'lambda':0,
					'K': 0
				}
				for i in range(min(sleep_cycle_length, boundary_group))
			}

			for i in device.childs:

				# find the minimum lambda group
				min_lambd = min([groups[G]['lambda'] for G in groups])
				min_lambd_G = [G for G in groups if groups[G]['lambda'] == min_lambd]
				min_lambd_G = random.choice(min_lambd_G)

				# append the device to the minimum lambda group
				# FIXME: performance issue
				groups[min_lambd_G]['device'].append(i)
				groups[min_lambd_G]['lambda'] += i.lambd[interface]
				groups[min_lambd_G]['K'] = LengthAwkSlpCyl(groups[min_lambd_G]['lambda'], DATA_TH)

			K = min([groups[G]['K'] for G in groups])

			if K == sleep_cycle_length:
				break
			elif len(groups) == boundary_group:
				sleep_cycle_length = K if K > 0 else sleep_cycle_length
				break
			else:
				sleep_cycle_length = K if K > 0 else sleep_cycle_length

		msg_execute("sleep cycle length = %d with %d groups" % \
			(sleep_cycle_length, len(groups)), pre=prefix)

		result = [[] for i in range(sleep_cycle_length)]
		for i in groups:
			groups[i]['device'] and groups[i]['device'].append(device)
			result[i] += groups[i]['device']

		return result

	except Exception as e:
		msg_fail(str(e), pre=prefix)
		return

def merge(device, duplex='FDD', two_hop=False):

	prefix = "lbps::merge::%s\t" % device.name

	try:
		# duplex will only affect the capacity, not related to mapping
		if duplex is not 'FDD' and duplex is not 'TDD':
			return

		if not isinstance(device, eNB) and not isinstance(device, RN):
			return

		interface = 'backhaul' if isinstance(device, eNB) else 'access'
		capacity = device.capacity if duplex == 'FDD' else device.virtualCapacity
		capacity = capacity[interface] if type(capacity) is dict else capacity
		pkt_size = getAvgPktSize(device)
		DATA_TH = int(getDataTH(capacity, pkt_size))
		msg_execute("load= %g\t" % getLoad(device, duplex), pre=prefix)
		required_backhaul_subframe = None

		# init merge groups
		groups = [
			{
				'device': [i],
				'lambda': i.lambd[interface],
				'K': 2**floor(log(LengthAwkSlpCyl(i.lambd[interface], DATA_TH), 2))
			} for i in device.childs
		]

		# merge process
		while True:
			check_list = [i['K'] for i in groups]

			if two_hop:
				Ki = max([G['K'] for G in groups])
				required_access_subframe = int(sum([Ki/G['K'] for G in groups]))
				required_backhaul_subframe = ceil(DATA_TH*required_access_subframe*pkt_size/device.virtualCapacity)
				if sum([1/KG for KG in check_list])+(required_backhaul_subframe/Ki)<=1:
					break

			elif schedulability(check_list):
				break

			# non-degraded merge
			groups.sort(key=lambda x: x['K'], reverse=True)
			g_non_degraded = non_degraded(groups, interface, DATA_TH)
			non_degraded_success = False if len(g_non_degraded) == len(groups) else True
			groups = g_non_degraded

			# degraded merge
			if not non_degraded_success and len(groups) > 1:
				groups[1]['device'] += groups[0]['device']
				groups[1]['lambda'] += groups[0]['lambda']
				groups[1]['K'] = LengthAwkSlpCyl(groups[1]['lambda'], DATA_TH)
				groups.pop(0)

		# calc the times of waking up for group
		max_K = max([G['K'] for G in groups])
		groups.sort(key=lambda x: x['K'])

		msg_execute("sleep cycle length = %d with %d groups" % \
				(max_K, len(groups)), pre=prefix)

		result = {i:[] for i in range(max_K)}

		for G in groups:
			base = 0
			for i in list(result.keys()):
				if not result[i]:
					base = i
					break
			for TTI in range(base, len(result), G['K']):
				result[TTI] = G['device'] + [device]

		a_result = list(result.values())

		if two_hop:
			b_result = [[device, device.parent]]*required_backhaul_subframe
			b_result.extend([[]]*(max_K-required_backhaul_subframe))
			return {'backhaul':b_result, 'access':a_result}

		return a_result

	except Exception as e:
		msg_fail(str(e), pre=prefix)
		return

"""[summary] proposed lbps algorithm

[description] for two hop in TDD with multiple RN and considering different CQI
"""

def min_aggr(device, simulation_time, check_K=False):
	prefix = "BottomUp::min-aggr\t"
	duplex = 'TDD'

	rn_status = {rn:{'Ai_result':aggr(rn, duplex)} for rn in device.childs}
	for rn in rn_status.keys():
		rate = rn.virtualCapacity/device.virtualCapacity
		rn_status[rn].update({
			'Ai_K':len(rn_status[rn]['Ai_result']),
			'Ai_count':1,
			'Bh_count':ceil(rate)
			})

	Bh_K = min([v['Ai_K'] for v in rn_status.values()])
	mincycle_shrinking(rn_status, Bh_K)
	Bh_check, Ai_check = mincycle_schedulability(rn_status, Bh_K)

	# scheduling
	Bh_result = [[] for i in range(Bh_K)]
	Ai_result = [[] for i in range(Bh_K)]
	if Bh_check and Ai_check:
		for rn in rn_status.keys():
			Bh = [device, rn]

			# backhaul
			for TTI in range(Bh_K):
				if Bh_result[TTI]: continue
				for i in range(rn_status[rn]['Bh_count']):
					Bh_result[TTI+i] += Bh
				break

			# access
			for i, TTI in enumerate(rn_status[rn]['Ai_result']):
				Ai_result[i] += TTI
	else:
		Bh_result, Ai_result = schedule_failed(device)

	if check_K:
		return get_sleep_cycle(device, Bh_result, Ai_result)

	mapping_pattern = m_2hop(device.tdd_config)
	timeline = two_hop_realtimeline(
		mapping_pattern,
		simulation_time,
		Bh_result,
		Ai_result)

	msg_warning("total awake: %d times" %\
		(sum([1 for i in timeline['backhaul'] if i])+\
		sum([1 for i in timeline['access'] if i])-\
		sum([1 for i in range(len(timeline['access'])) \
			if timeline['backhaul'][i] and timeline['access'][i]]
	)), pre=prefix)

	return timeline

def min_split(device, simulation_time, check_K=False):
	prefix = "BottomUp::min-split\t"
	duplex = 'TDD'

	rn_status = {rn:{'Ai_result':split(rn, duplex)} for rn in device.childs}
	for rn in rn_status.keys():
		rate = rn.virtualCapacity/device.virtualCapacity
		rn_status[rn].update({
			'Ai_K': len(rn_status[rn]['Ai_result']),
			'Ai_count':sum([1 for TTI in rn_status[rn]['Ai_result'] if TTI])
			})
		rn_status[rn].update({'Bh_count':ceil(rn_status[rn]['Ai_count']*rate)})

	Bh_K = min([v['Ai_K'] for v in rn_status.values()])
	mincycle_shrinking(rn_status, Bh_K)
	Bh_result = [[] for i in range(Bh_K)]
	Ai_result = [[] for i in range(Bh_K)]

	# scheduling
	while True:
		Bh_check, Ai_check = mincycle_schedulability(rn_status, Bh_K)
		if Bh_check and Ai_check:
			for rn in rn_status.keys():
				Bh = [device, rn]

				for TTI in range(Bh_K):
					if Bh_result[TTI]: continue
					for i in range(rn_status[rn]['Bh_count']):
						Bh_result[TTI+i] += Bh
					break

				for i, TTI in enumerate(rn_status[rn]['Ai_result']):
					Ai_result[i] += TTI
			break
		else:
			# choose the target of reversing split
			r_rn = None
			for rn in rn_status.keys():
				if rn_status[rn]['Ai_K'] == Bh_K\
				and rn_status[rn]['Ai_count']>1:
					r_rn = rn
					break

			if not r_rn:
				Bh_result, Ai_result = schedule_failed(device)
				break

			groups = rn_status[r_rn]['Ai_count']
			rn_status[r_rn].update({
				'Ai_result':split(r_rn, duplex, groups-1)
				})
			rn_status[r_rn].update({
				'Ai_K': len(rn_status[r_rn]['Ai_result']),
				'Ai_count':sum([1 for TTI in rn_status[r_rn]['Ai_result'] if TTI])
				})
			Bh_K = rn_status[r_rn]['Ai_K']
			mincycle_shrinking(rn_status, Bh_K)

	if check_K:
		return get_sleep_cycle(device, Bh_result, Ai_result)

	mapping_pattern = m_2hop(device.tdd_config)
	timeline = two_hop_realtimeline(
		mapping_pattern,
		simulation_time,
		Bh_result,
		Ai_result)

	msg_warning("total awake: %d times" %\
		(sum([1 for i in timeline['backhaul'] if i])+\
		sum([1 for i in timeline['access'] if i])-\
		sum([1 for i in range(len(timeline['access'])) \
			if timeline['backhaul'][i] and timeline['access'][i]]
	)), pre=prefix)

	return timeline

def merge_merge(device, simulation_time, check_K=False):
	prefix = "BottomUp::merge-merge\t"
	duplex = 'TDD'

	rn_status = {rn:{'Ai_result':merge(rn, duplex)} for rn in device.childs}
	for rn in rn_status.keys():
		rate = rn.virtualCapacity/device.virtualCapacity
		rn_status[rn].update({
			'Ai_K':len(rn_status[rn]['Ai_result']),
			'Ai_count':sum([1 for TTI in rn_status[rn]['Ai_result'] if TTI])
			})
		rn_status[rn].update({'Bh_count':rn_status[rn]['Ai_count']*rate})

	# backhaul merge
	groups = [{
		'device':[rn],
		'Ai_K':rn_status[rn]['Ai_K'],
		'Bh_count':rn_status[rn]['Bh_count']
		} for rn in rn_status.keys()]

	while sum([ceil(i['Bh_count'])/i['Ai_K'] for i in groups])>1:
		groups.sort(key=lambda x:x['Ai_K'], reverse=True)
		non_degraded_success = False
		for source_G in groups:
			for target_G in groups:
				if target_G is not source_G\
				and target_G['Ai_K'] == source_G['Ai_K']\
				and ceil(target_G['Bh_count']+source_G['Bh_count'])<source_G['Ai_K']:
					# check access schedulability respectively
					target_Ai = sum([\
						sum([1 for TTI in rn_status[rn]['Ai_result'] if TTI])\
						for rn in target_G['device']])
					source_Ai = sum([\
						sum([1 for TTI in rn_status[rn]['Ai_result'] if TTI])\
						for rn in source_G['device']])
					if target_Ai+source_Ai>source_G['Ai_K']: break

					non_degraded_success=True
					source_G['device'] += target_G['device']
					source_G['Bh_count'] += target_G['Bh_count']
					groups.remove(target_G)
					break
			else: continue
			break

		if not non_degraded_success: break

	# schedulability
	Ai_check = []
	for g in groups:
		Ai_count = sum([rn_status[rn]['Ai_count'] for rn in g['device']])
		check = True if Ai_count+ceil(g['Bh_count'])<=g['Ai_K'] else False
		Ai_check.append(check)
	Ai_check = all(Ai_check)
	Bh_K = max([v['Ai_K'] for v in rn_status.values()])
	Bh_check =\
	True if sum([ceil(i['Bh_count'])/i['Ai_K']\
		for i in groups])<=1 else False

	# scheduling
	Bh_result = [[] for i in range(Bh_K)]
	Ai_result = [[] for i in range(Bh_K)]
	if Bh_check and Ai_check:
		for g in groups:

			# backhaul
			Bh = [rn for rn in g['device']]
			Bh.append(device)
			TTI = 0
			while TTI<len(Bh_result):
				if Bh_result[TTI]:
					TTI += 1
					continue
				for count in range(ceil(g['Bh_count'])):
					Bh_result[TTI+count] += Bh
				TTI += g['Ai_K']

			# access
			Ai_group_result = [[] for i in range(g['Ai_K'])]
			for rn in g['device']:
				for TTI, v in enumerate(Ai_group_result):
					Ai_group_result[TTI] += rn_status[rn]['Ai_result'][TTI]

			for i, v in enumerate(Ai_group_result):
				Ai_result[i] += v
	else:
		Bh_result, Ai_result = schedule_failed(device)

	if check_K:
		return get_sleep_cycle(device, Bh_result, Ai_result)

	mapping_pattern = m_2hop(device.tdd_config)
	timeline = two_hop_realtimeline(
		mapping_pattern,
		simulation_time,
		Bh_result,
		Ai_result)

	msg_warning("total awake: %d times" %\
		(sum([1 for i in timeline['backhaul'] if i])+\
		sum([1 for i in timeline['access'] if i])-\
		sum([1 for i in range(len(timeline['access'])) \
			if timeline['backhaul'][i] and timeline['access'][i]]
	)), pre=prefix)

	return timeline

def top_down(b_lbps, device, simulation_time, check_K=False):
	prefix = "TopDown::TD-%s \t" % (b_lbps)
	duplex = 'TDD'
	lbps_scheduling = {
		'aggr': aggr,
		'split': split,
		'merge': merge
	}

	def access_scheduling(device, lbps_result):
		Bh_K = len(lbps_result)
		rn_stauts = {
			rn:{
				'Ai_K':int(Bh_K/sum([1 for TTI in lbps_result if rn in TTI])),
				'Bh_count':sum([1 for TTI in lbps_result if rn in TTI]),
				'Ai_count':ceil(device.virtualCapacity/rn.virtualCapacity)
			}
			for rn in device.childs
		}

		# check access schedulability
		# TD do not need check ackhaul schedulability
		check = []
		for rn in device.childs:
			if rn_stauts[rn]['Ai_count']+1<=rn_stauts[rn]['Ai_K']:
				check.append(True)
			else:
				check.append(False)

		# scheduling failed
		if not all(check):
			Bh_result = [rn for rn in device.childs]
			Bh_result.append(device)
			Bh_result = [Bh_result]*Bh_K
			Ai_result = [ue for rn in device.childs for ue in rn.childs]
			Ai_result += device.childs
			Ai_result = [Ai_result]*Bh_K
			return Bh_result, Ai_result

		# have schedulability
		Bh_result = lbps_result
		Ai_result = [[] for i in range(Bh_K)]
		for rn in device.childs:
			Ai_rn_result = [ue for ue in rn.childs]
			Ai_rn_result.append(rn)
			for cycle_start in range(0, Bh_K, rn_stauts[rn]['Ai_K']):
				for TTI in range(rn_stauts[rn]['Ai_count']):
					Ai_result[cycle_start+TTI] += Ai_rn_result

		return Bh_result, Ai_result

	try:
		lbps_result = lbps_scheduling[b_lbps](device, duplex)
		Bh_result, Ai_result = access_scheduling(device, lbps_result)
		mapping_pattern = m_2hop(device.tdd_config)

		if check_K:
			return get_sleep_cycle(device, Bh_result, Ai_result)

		timeline = two_hop_realtimeline(
			mapping_pattern,
			simulation_time,
			Bh_result,
			Ai_result)

		for i in range(len(timeline['backhaul'])):
			timeline['backhaul'][i] = list(set(timeline['backhaul'][i]))
			timeline['access'][i] = list(set(timeline['access'][i]))

		msg_warning("total awake: %d times" %\
			(sum([1 for i in timeline['backhaul'] if i])+\
			sum([1 for i in timeline['access'] if i])-\
			sum([1 for i in range(len(timeline['access'])) \
				if timeline['backhaul'][i] and timeline['access'][i]]
		)), pre=prefix)

		return timeline

	except Exception as e:
		msg_fail(str(e), pre=prefix)
		return

def bottom_up(a_lbps, device, simulation_time, check_K=False):
	prefix = "BottomUp::%s \t" % (a_lbps)
	lbps_scheduling = {
		'aggr': min_aggr,
		'split': min_split,
		'merge': merge_merge
	}

	# try:
	return lbps_scheduling[a_lbps](device, simulation_time, check_K)

	# except Exception as e:
	# 	msg_fail(str(e), pre=prefix)
	# 	return