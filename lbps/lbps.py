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
	result and msg_success("Check schedulability:\tTrue")
	not result and msg_warning("Check schedulability:\tFalse")

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
			i['device'].append(source_G)
			i['lambda'] += source_G['lambda']

	not result and G.append(source_G)
	return G.sort(key=lambda x: x['K'], reverse=True)

def access_aggr(device, b_result):

	if b_result:
		lbps_failed = []

		for rn in device.childs:
			b_TTI = None
			a_subframe = ceil(device.capacity/rn.capacity['access'])

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

def aggr(device, duplex='FDD', show=False):

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

def split(device, duplex='FDD', show=False):

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
		load = getLoad(device, duplex)

		if load > 1:
			msg_fail("load= %g\t, scheduling failed!!!!!!!!!!" % load, pre=prefix)
			return False

		msg_execute("load= %g\t" % load, pre=prefix)
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

		# encapsulate result: { subframe: wakeUpDevice }
		result = {i+1:None for i in range(sleep_cycle_length)}
		for i in groups:
			groups[i]['device'] and groups[i]['device'].append(device)
			result[i] = groups[i]['device'] if groups[i]['device'] else None

		return result

	except Exception as e:
		msg_fail(str(e), pre=prefix)
		return

def merge(device, duplex='FDD', show=False):

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
		load = getLoad(device, duplex)

		if load > 1:
			msg_fail("load= %g\t, scheduling failed!!!!!!!!!!" % load, pre=prefix)
			return False

		msg_execute("load= %g\t" % load, pre=prefix)


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
			if non_degraded_success and len(groups) > 1:
				groups[1]['deivce'] += groups[0]['device']
				groups[1]['lambda'] += groups[0]['lambda']
				groups[1]['K'] = LengthAwkSlpCyl(groups[1]['lambda'], DATA_TH)
				groups.pop(0)

		# calc the times of waking up for group
		max_K = max([G['K'] for G in groups])
		groups.sort(key=lambda x: x['K'])

		# encapsulate result: { subframe: wakeUpDevice }
		result = {i+1:None for i in range(max_K)}

		for G in groups:
			base = 0

			for i in list(result.keys()):
				if result[i] is None:
					base = i
					break

			for TTI in range(base, len(result), G['K']):
				result[TTI] = G['device'] + [device]

		return result

	except Exception as e:
		msg_fail(str(e), pre=prefix)
		return

def aggr_aggr(device, simulation_time, duplex='TDD'):
	prefix = "lbps::aggr-aggr::%s \t" % device.name

	try:
		lbps_result = aggr(device, duplex)
		b_lbps_result = [[j.name for j in i] for i in lbps_result]
		lbps_failed = access_aggr(device, lbps_result)
		a_lbps_result = [[j.name for j in i] for i in lbps_result]
		a_lbps_result = [list(set(a_lbps_result[i])-set(b_lbps_result[i]))\
						for i in range(len(a_lbps_result))]

		mapping_pattern = m_2hop(device.tdd_config)
		timeline = [[] for i in range(simulation_time)]

		# extend and align timeline
		vt_mapping = {'backhaul':[], 'access':[]}
		for i in range(ceil(simulation_time/10)):
			vt_mapping['backhaul'] += [[i*10+v for v in su] for su in mapping_pattern['backhaul']]
			vt_mapping['access'] += [{
				'identity':su['identity'],
				'TTI': [i*10+v for v in su['r_TTI']]} for su in mapping_pattern['access']]

		b_lbps_result = [getDeviceByName(device, i) for i in b_lbps_result]
		b_lbps_result *= ceil(simulation_time/len(b_lbps_result))
		a_lbps_result = [getDeviceByName(device, i) for i in a_lbps_result]
		a_lbps_result *= ceil(simulation_time/len(a_lbps_result))

		# backhaul mapping
		for i in range(simulation_time):
			for rsb in vt_mapping['backhaul'][i]:
				timeline[rsb] += b_lbps_result[i]
				timeline[rsb] += lbps_failed

		# access mapping
		for i in range(0, simulation_time, len(lbps_result)):
			tmp_map = {'access':[], 'mixed':[], 'backhaul':[]}
			for j in vt_mapping['access'][i:i+len(lbps_result)]:
				tmp_map[j['identity']].append(j)
			for vt in a_lbps_result[i:i+len(lbps_result)]:
				if not vt:
					continue

				identity = 'backhaul' if tmp_map['backhaul'] else None
				identity = 'mixed' if tmp_map['mixed'] else identity
				identity = 'access' if tmp_map['access'] else identity

				for rsb in tmp_map[identity][0]['TTI']:
					timeline[rsb] += vt
				for fail_rn in lbps_failed:
					timeline[rsb] += fail_rn
					timeline[rsb] += fail_rn.childs

				tmp_map[identity].pop(0)

		for i in range(len(timeline)):
			timeline[i] = list(set(timeline[i]))

		return timeline

	except Exception as e:
		msg_fail(str(e), pre=prefix)
		return