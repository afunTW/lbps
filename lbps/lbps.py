import copy
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
		return

def getAvgPktSize(device):
	interface = 'backhaul' if isinstance(device, eNB) else 'access'
	total_pkt = [bearer.flow for bearer in device.link[interface]]
	total_pkt = [traffic[i]['pkt_size'] for i in total_pkt]
	return sum(total_pkt)/len(total_pkt)

def schedulability(check_list):

	result = True if sum([1/cycle for cycle in check_list]) <= 1 else False;

	if result:
		msg_success("Check schedulability:\tTrue")

	else:
		msg_warning("Check schedulability:\tFalse")

	return result

def non_degraded(G1, G2, interface, DATA_TH):

	# calc the load of merged group
	# merged_group = G1['devices'] + G2['devices']
	# merged_load = getLoad(merged_group, interface)

	# calc the sleepCycle of merged group
	# check if the sleepCycle still the same

	sleep_cycle_length_1 = LengthAwkSlpCyl(sum([i.lambd[interface] for i in G1]), DATA_TH)
	sleep_cycle_length_1 = 2**floor(log(sleep_cycle_length_1, 2))
	sleep_cycle_length_2 = LengthAwkSlpCyl(sum([i.lambd[interface] for i in G2]), DATA_TH)
	sleep_cycle_length_2 = 2**floor(log(sleep_cycle_length_2, 2))

	merge_sleep_cycle = LengthAwkSlpCyl(sum([i.lambd[interface] for i in G1 + G2]), DATA_TH)
	merge_sleep_cycle = 2**floor(log(merge_sleep_cycle, 2))

	result = True if merge_sleep_cycle in [sleep_cycle_length_1, sleep_cycle_length_2] else False
	return result

def aggr(device, duplex='FDD', show='False'):

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

def split(device, interface, duplex='FDD'):

	prefix = "lbps::split::%s\t" % device.name

	try:
		# init
		capacity = getCapacity(device, interface, duplex)
		DATA_TH = getDataTH(capacity, device.link[interface][0].pkt_size)
		load = getLoad(device, interface)

		if load < 1:
			msg_success("load= %g\t" % load, pre=prefix)

			sleep_cycle_length = LengthAwkSlpCyl(device.lambd[interface], DATA_TH)
			groups = [copy.deepcopy(device.childs)]
			old_groupsLength = 0

			# Split process
			while old_groupsLength is not len(groups):
				old_groupsLength = len(groups)
				groups = [[] for i in range(min(sleep_cycle_length, len(device.childs)))]
				groups_load = [0 for i in range(len(groups))]
				groups_K = [0 for i in range(len(groups))]

				for i in device.childs:
					min_load = groups_load.index(min(groups_load))
					groups[min_load].append(i)
					groups_load[min_load] += i.lambd[interface]
					groups_K[min_load] = LengthAwkSlpCyl(groups_load[min_load], DATA_TH)

				sleep_cycle_length = min(groups_K) if min(groups_K) > 0 else sleep_cycle_length

			msg_success("sleep cycle length = %d with %d groups" % (sleep_cycle_length, len(groups)), pre=prefix)

			# record
			device.sleepCycle = sleep_cycle_length
			for i in range(len(groups)):
				for j in groups[i]:
					j.sleepCycle = groups_K[i]
					j.lbpsGroup = i
					j.wakeUpTimes = 1

			"""
			encapsulate:
			{
				subframe: {
					'devices': wakeUpDevice,
					'load': groupLoad,
					'sleepCycle': groupRealSleepCycle
				}
			}
			"""
			result = {i:None for i in range(sleep_cycle_length)}
			for i in range(len(groups)):
				G = {
					'devices': groups[i],
					'load': groups_load[i],
					'sleepCycle': groups_K[i]
				}
				result[i] = G

			return result

		else:
			msg_fail("load= %g\t, scheduling failed!!!!!!!!!!" % load, pre=prefix)
			sleep_cycle_length = 1
			device.sleepCycle = sleep_cycle_length

			for i in device.childs:
				i.sleepCycle = sleep_cycle_length

			return

	except Exception as e:
		msg_fail(str(e), pre=prefix)
		return

def merge(device, interface, duplex='FDD'):

	prefix = "lbps::merge::%s\t" % device.name

	try:
		# init
		capacity = getCapacity(device, interface, duplex)
		DATA_TH = getDataTH(capacity, device.link[interface][0].pkt_size)
		load = getLoad(device, interface)

		if load < 1:
			msg_success("load= %g\t" % load, pre=prefix)

			# init merge groups
			groups = {
				i:{
					'devices': [device.childs[i]],
					'load': device.childs[i].lambd[interface],
					'sleepCycle': LengthAwkSlpCyl(device.childs[i].lambd[interface], DATA_TH)
				} for i in range(len(device.childs))
			}

			for i in groups:
				groups[i]['sleepCycle'] = 2**floor(log(groups[i]['sleepCycle'], 2))

			non_degraded(groups[0], groups[1], interface, DATA_TH)

			# # merge process
			# while not schedulability([groups[i]['sleepCycle'] for i in groups]):

			# 	# find the merge group
			# 	min_load_group = min([groups[i]['sleepCycle'] for i in groups])
			# 	for i in groups:
			# 		if groups[i]['sleepCycle'] == min_load_group:
			# 			min_load_group = groups[i]
			# 			break

			# 	# non-degraded merge
			# 	non_degraded_success = False
			# 	for i in groups:
			# 		if i == min_load_group:
			# 			continue
			# 		if non_degraded(min_load_group, i, interface, DATA_TH):
			# 			non_degraded_success = True

			# groups = [[i] for i in device.childs]
			# groups_load = [i.lambd[interface] for i in device.childs]
			# K_original = [LengthAwkSlpCyl(i, DATA_TH) for i in groups_load]
			# K_merge = list(map(lambda x: 2**floor(log(x, 2)), K_original))

			# # merge process
			# while not schedulability(K_merge):
			# 	min_load = groups_load.index(min(groups_load))

			# 	# non-degraded merge
			# 	non_degraded_success = False
			# 	for i in groups:
			# 		if i is groups[min_load]:
			# 			continue
			# 		if non_degraded(groups[min_load], i, interface, DATA_TH):
			# 			non_degraded_success = True
			# 			i += groups[min_load]
			# 			del groups[min_load]
			# 			break

			# 	# degraded merge
			# 	if not non_degraded_success and len(groups) > 1:
			# 		msg_execute("degraded merge process", pre=prefix)

			# 		groups = [d for (k,d) in sorted(zip(K_merge, groups), key=lambda x: x[0], reverse=True)]
			# 		groups[0] += groups[1]
			# 		del groups[1]

			# 		K_merge = [sum([dev.lambd[interface] for dev in subgroup]) for subgroup in groups]
			# 		K_merge = [LengthAwkSlpCyl(i, DATA_TH) for i in K_merge]
			# 		K_merge = list(map(lambda x: 2**floor(log(x, 2)), K_merge))

			# 	elif non_degraded_success and len(groups) > 1:
			# 		msg_execute("non-degraded merge process", pre=prefix)
			# 	else:
			# 		msg_warning("reamain only one group", pre=prefix)

			# msg_success("sleep cycle length = %d with %d groups" % (max(K_merge), len(groups)), pre=prefix)

			# # record
			# device.sleepCycle = max(K_merge)
			# for i in range(len(groups)):
			# 	for j in groups[i]:
			# 		j.sleepCycle = K_merge[i]
			# 		j.lbpsGroup = i
			# 		j.wakeUpTimes = int(max(K_merge)/K_merge[i])
			# 		j.wakeUpTimes

			# """
			# encapsulate:
			# {
			# 	subframe: {
			# 		'devices': wakeUpDevice,
			# 		'load': groupLoad,
			# 		'sleepCycle': groupRealSleepCycle
			# 		'wakeUpTimes': groupWakeUpTimes
			# 	}
			# }
			# """
			# result = {i:None for i in range(sleep_cycle_length)}
			# print(len(groups))
			# print(len(groups_load))
			# print(len(K_merge))

			# return K_merge

		else:
			msg_fail("load= %g\t, scheduling failed!!!!!!!!!!" % load, pre=prefix)
			sleep_cycle_length = 1
			device.sleepCycle = sleep_cycle_length

			for i in device.childs:
				i.sleepCycle = sleep_cycle_length

			return

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