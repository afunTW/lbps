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

def getDeviceByName(device, name_list):
	result = []
	d = {
		'eNB':device,
		'RN':[rn for rn in device.childs],
		'UE':[ue for rn in device.childs for ue in rn.childs]
	}

	for i in name_list:
		if re.search('eNB*', i):
			result.append(device)
		elif re.search('RN*', i):
			for rn in d['RN']:
				if rn.name == i:
					result.append(rn)
					break
		elif re.search('UE*', i):
			for ue in d['UE']:
				if ue.name == i:
					result.append(ue)
					break
	return result

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

def access_aggr(device, b_result):

	if b_result:
		lbps_failed = []

		for rn in device.childs:
			b_TTI = None
			a_subframe = ceil(device.virtualCapacity/rn.virtualCapacity)

			if a_subframe > len(b_result)-1:
				lbps_failed.append(rn)
				continue

			for i in b_result:
				if a_subframe == 0:
					break
				if rn in i:
					continue
				i += rn.childs
				i.append(rn)
				a_subframe -= 1

		return lbps_failed

	return

def two_hop_realtimeline(mapping_pattern, t, b, a, k):

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

		# Split process
		while len(groups) < sleep_cycle_length:

			groups = {
				i:{
					'device': [],
					'lambda':0,
					'K': 0
				}
				for i in range(min(sleep_cycle_length, len(device.childs)))
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

def merge(device, duplex='FDD'):

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

		# init merge groups
		groups = [
			{
				'device': [i],
				'lambda': i.lambd[interface],
				'K': 2**floor(log(LengthAwkSlpCyl(i.lambd[interface], DATA_TH), 2))
			} for i in device.childs
		]

		# merge process
		while not schedulability([i['K'] for i in groups]):

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
		tmp = []

		for G in groups:
			base = 0

			for i in list(result.keys()):
				if not result[i]:
					base = i
					break

			for TTI in range(base, len(result), G['K']):
				result[TTI] = G['device'] + [device]

		for i in result:
			tmp.append(result[i])

		return tmp

	except Exception as e:
		msg_fail(str(e), pre=prefix)
		return

def top_down(b_lbps, device, simulation_time, duplex='TDD'):
	prefix = "TopDown::%s-aggr\t" % (b_lbps)
	lbps_scheduling = {
		'aggr': aggr,
		'split': split,
		'merge': merge
	}

	try:
		lbps_result = lbps_scheduling[b_lbps](device, duplex)
		b_lbps_result = [[j.name for j in i] for i in lbps_result]
		lbps_failed = access_aggr(device, lbps_result)
		a_lbps_result = [[j.name for j in i] for i in lbps_result]
		a_lbps_result = [list(set(a_lbps_result[i])-set(b_lbps_result[i]))\
						for i in range(len(a_lbps_result))]

		mapping_pattern = m_2hop(device.tdd_config)
		b_lbps_result = [getDeviceByName(device, i) for i in b_lbps_result]
		a_lbps_result = [getDeviceByName(device, i) for i in a_lbps_result]

		timeline = two_hop_realtimeline(
			mapping_pattern,
			simulation_time,
			b_lbps_result,
			a_lbps_result,
			len(lbps_result))

		for rn in lbps_failed:
			for TTI in range(len(timeline['backhaul'])):
				if device.tdd_config[TTI%10] == 'D':
					timeline['backhaul'][TTI].append(device)
					timeline['backhaul'][TTI].append(rn)
				if rn.tdd_config[TTI%10] == 'D':
					timeline['access'][TTI].append(rn)
					timeline['access'][TTI] += rn.childs


		for i in range(len(timeline['backhaul'])):
			timeline['backhaul'][i] = list(set(timeline['backhaul'][i]))
			timeline['access'][i] = list(set(timeline['access'][i]))

		msg_warning("backhaul awake: %d times" % sum([1 for i in timeline['backhaul'] if i]), pre=prefix)
		msg_warning("access awake: %d times" % sum([1 for i in timeline['access'] if i]), pre=prefix)
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

def min_aggr(device, simulation_time, duplex='TDD'):
	prefix = "BottomUp::min-aggr::%s\t" % (device.name)

	try:
		a_lbps_result = [aggr(rn, duplex) for rn in device.childs]
		b_min_cycle = min([len(i) for i in a_lbps_result])

	except Exception as e:
		msg_fail(str(e), pre=prefix)