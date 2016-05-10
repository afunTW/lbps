import random
from math import log, floor, ceil
from tdd import one_to_one_first_mapping as M3
from tdd import one_to_one_first_mapping_2hop as M3_2hop
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
		for rn in device.childs:
			b_TTI = None
			a_subframe = ceil(rn.capacity['access']/device.capacity)

			# find the backhaul transmission time
			for i in list(reversed(list(b_result.keys()))):
				if b_result[i] and rn in b_result[i]:
					b_TTI = i
					break

			# find the access transmission time
			if not b_TTI:
				raise Exception("backhaul scheduling goes wrong")

			trace = [(b_TTI+i-1)%len(b_result)+1 for i in b_result]
			trace = trace[0:a_subframe]
			queue = [ch for ch in rn.childs]
			queue.append(rn)

			for i in trace:
				b_result[i] = b_result[i]+queue if b_result[i] else queue

def two_hop_mapping(device, schedule_result):

	# align
	mapping_result = [i for i in list(schedule_result.keys())]
	padding = ceil(len(mapping_result)/10)*10-len(mapping_result)
	padding = [None for i in range(padding)]
	mapping_result += padding

	cycle = {i:[] for i in range(1,1+len(mapping_result))}
	mapping_pattern = [[] for i in range(len(cycle))]

	# TDD mapping
	b_mapping = [i for i in device.tdd_config]
	a_mapping = [i for i in device.childs[0].tdd_config]

	for i in range(len(a_mapping)):
		a_mapping[i] = None if a_mapping[i] is device.tdd_config[i] else a_mapping[i]

	b_mapping = list(reversed(M3(b_mapping)))
	a_mapping = list(reversed(M3(a_mapping)))

	for i in range(10):
		b_mapping[i] = b_mapping[i] if device.tdd_config[i] else None
		a_mapping[i] = a_mapping[i] if not device.tdd_config[i] else None

	for i in range(len(mapping_pattern)):
		if i%10 is 0 and i is not 0:
			b_mapping = list(map(lambda x: list(map(lambda y: y+10, x)) if x else None, b_mapping))
			a_mapping = list(map(lambda x: list(map(lambda y: y+10, x)) if x else None, a_mapping))
		mapping_pattern[i] += b_mapping[i%10] if b_mapping[i%10] else a_mapping[i%10]

	keys = list(schedule_result.keys())

	for i in range(len(keys)):
		if schedule_result[keys[i]]:
			for sf in mapping_pattern[i]:
				cycle[sf] += schedule_result[keys[i]]

	for i in cycle:
		cycle[i] = cycle[i] if cycle[i] else None

	return cycle

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
		load = getLoad(device, duplex)

		if load > 1:
			msg_fail("load= %g\t, scheduling failed!!!!!!!!!!" % load, pre=prefix)
			return False

		msg_execute("load= %g\t" % load, pre=prefix)

		# aggr process
		sleep_cycle_length = LengthAwkSlpCyl(device.lambd[interface], DATA_TH)
		msg_execute("sleepCycle = %d" % sleep_cycle_length ,pre=prefix)

		# encapsulate result: { subframe: wakeUpDevice }
		result = {i+1:None for i in range(sleep_cycle_length)}
		result[1] = [i for i in device.childs]
		result[1].append(device)
		result[1] = sorted(result[1], key=lambda d: d.name)

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

def aggr_aggr(device, duplex='TDD', show=False):
	prefix = "lbps::aggr-aggr::%s \t" % device.name

	try:

		# backhaul lbps
		b_result = aggr(device, duplex)

		# access scheduliability
		# future work: if subframe_count > 1 can optimize by split in specfic cycle length
		access_aggr(device, b_result)

		# mapping to real timeline
		timeline = two_hop_mapping(device, b_result)

		return timeline

	except Exception as e:
		msg_fail(str(e), pre=prefix)
		return