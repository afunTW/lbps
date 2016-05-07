import random
from math import log, floor
from tdd import one_to_one_first_mapping as M3
from tdd import one_to_one_first_mapping_2hop as M3_2hop
from device import UE, RN, eNB

from poisson import getDataTH, LengthAwkSlpCyl, DataAcc
from config import *
from viewer import *
from pprint import pprint

"""[summary] supported function

[description]
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
			result[i+1] = groups[i]['device'] if groups[i]['device'] else None

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
		# groups.extend([G for G in groups for i in range(int((max_K/G['K'])-1))])
		groups.sort(key=lambda x: x['K'])

		# encapsulate result: { subframe: wakeUpDevice }
		result = {i+1:None for i in range(max_K)}

		for G in groups:
			base = 0

			for i in result:
				if result[i] is None:
					base = i
					break

			for TTI in range(base, max_K+1, G['K']):
				result[TTI] = G


		return result

	except Exception as e:
		msg_fail(str(e), pre=prefix)
		return

def aggr_aggr(device, interface, duplex='FDD'):
	prefix = "lbps::aggr-aggr::%s \t" % device.name

	try:

		# backhaul lbps
		backhaul_K = aggr(device, interface, duplex)

		# access scheduliability
		# future work: if subframe_count > 1 can optimize by split in specfic cycle length
		for i in device.childs:
			capacity = getCapacity(device, interface, duplex)
			DATA_TH = getDataTH(capacity, device.link[interface][0].pkt_size)
			access_K = DataAcc(i.lambd[interface], backhaul_K)
			subframe_count = int((access_K/DATA_TH)+1)

			if subframe_count > backhaul_K:
				raise Exception("%s: scheduling failed" % i.name)

			if subframe_count > 1:
				msg_warning("%s: wake up %d subframe" % (i.name, subframe_count), pre=prefix)

			i.sleepCycle = backhaul_K

			for j in i.childs:
				j.sleepCycle = backhaul_K
				j.wakeUpTimes = subframe_count

		return backhaul_K

	except Exception as e:
		msg_fail(str(e), pre=prefix)
		return