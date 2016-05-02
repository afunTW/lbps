import copy
from math import log, floor
from tdd import one_to_one_first_mapping as M3
from tdd import one_to_one_first_mapping_2hop as M3_2hop
from device import UE, RN, eNB

from poisson import getDataTH, LengthAwkSlpCyl, DataAcc
from config import bcolors
from viewer import *

"""[summary] supported function

[description]
"""

def getLoad(device, interface, duplex="FDD"):

	try:
		RSC = device.capacity[interface]
		capacity = device.virtualCapacity[interface] if duplex == "TDD" else RSC
		return device.lambd[interface]/(capacity/device.link[interface][0].pkt_size)

	except Exception as e:
		msg_fail(str(e), pre="%s::getLoad\t\t" % device.name)
		return

def getCapacity(device, interface, duplex):

	try:
		duplex = duplex.upper() if type(duplex) is str else ""

		if duplex == 'FDD':
			return device.capacity[interface]

		elif duplex == 'TDD':
			return device.virtualCapacity[interface]

		else:
			return 0

	except Exception as e:
		msg_fail(str(e), pre="%s::getCapacity\t" % device.name)

def schedulability(check_list):

	result = True if sum([1/cycle for cycle in check_list]) <= 1 else False;

	if result:
		msg_success("Check schedulability:\tTrue")

	else:
		msg_warning("Check schedulability:\tFalse")

	return result

def non_degraded(groups_1, groups_2, interface, DATA_TH):

	sleep_cycle_length_1 = LengthAwkSlpCyl(sum([i.lambd[interface] for i in groups_1]), DATA_TH)
	sleep_cycle_length_1 = 2**floor(log(sleep_cycle_length_1, 2))
	sleep_cycle_length_2 = LengthAwkSlpCyl(sum([i.lambd[interface] for i in groups_2]), DATA_TH)
	sleep_cycle_length_2 = 2**floor(log(sleep_cycle_length_2, 2))

	merge_sleep_cycle = LengthAwkSlpCyl(sum([i.lambd[interface] for i in groups_1 + groups_2]), DATA_TH)
	merge_sleep_cycle = 2**floor(log(merge_sleep_cycle, 2))

	result = True if merge_sleep_cycle in [sleep_cycle_length_1, sleep_cycle_length_2] else False
	return result

def load_based_power_saving(device, access, backhaul=None, TDD=False, show=False):

	try:
		# NOTE: this process can not use in direct link (eNB-UE)
		interface = 'backhaul' if isinstance(device, eNB) else 'access'
		scheduling = backhaul+'-'+access if backhaul else access
		check = scheduling in LBPS_scheduling.keys()
		result = None

		if check and not TDD:
			K = LBPS_scheduling[scheduling](device, interface, duplex='FDD')
			return result_mapping[scheduling](device, show) if K else None

		elif check and TDD:
			K = LBPS_scheduling[scheduling](device, interface, duplex='TDD')

			if not K:
				return

			# two hop, TopDown
			if backhaul:
				result = result_mapping[scheduling](device, backhaul, show=False)
				map_result = M3_2hop(device, interface, result)
				return result_mapping[scheduling+'-tdd'](device, result, map_result, show)

			# one hop
			else:
				result = result_mapping[scheduling](device, show=False)
				map_result = M3(device, interface, result)
				return result_mapping[scheduling+'-tdd'](device, result, map_result, show)

	except Exception as e:
		msg_fail(str(e), pre="schedule_result\t\t")
		return

"""[summary] basic LBPS scheduling

[description]
"""

def aggr(device, interface, duplex='FDD'):

	prefix = "lbps::aggr::%s \t" % device.name

	try:
		capacity = getCapacity(device, interface, duplex)
		DATA_TH = getDataTH(capacity, device.link[interface][0].pkt_size)
		load = getLoad(device, interface)

		if load < 1:
			msg_success("load= %g\t" % load, pre=prefix)
			sleep_cycle_length = LengthAwkSlpCyl(device.lambd[interface], DATA_TH)

			# record
			for i in device.childs:
				i.sleepCycle = sleep_cycle_length
				i.wakeUpTimes = 1
				# msg_execute("%s.sleepCycle = %d" % (i.name, i.sleepCycle), pre=prefix)

			device.sleepCycle = sleep_cycle_length
			msg_success("sleepCycle = %d" % i.sleepCycle ,pre=prefix)
			return sleep_cycle_length

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

			# record
			for i in range(len(groups)):
				for j in groups[i]:
					j.sleepCycle = groups_K[i]
					j.lbpsGroup = i
					j.wakeUpTimes = 1
					# msg_execute("%s.sleepCycle = %d\tin Group %d" % (j.name, j.sleepCycle, j.lbpsGroup), pre=prefix)

			msg_success("sleep cycle length = %d with %d groups" % (sleep_cycle_length, len(groups)), pre=prefix)
			device.sleepCycle = sleep_cycle_length
			return sleep_cycle_length

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

			groups = [[i] for i in device.childs]
			groups_load = [i.lambd[interface] for i in device.childs]
			K_original = [LengthAwkSlpCyl(i, DATA_TH) for i in groups_load]
			K_merge = list(map(lambda x: 2**floor(log(x, 2)), K_original))

			# merge process
			while not schedulability(K_merge):
				min_load = groups_load.index(min(groups_load))

				# non-degraded merge
				non_degraded_success = False
				for i in groups:
					if i is groups[min_load]:
						continue
					if non_degraded(groups[min_load], i, interface, DATA_TH):
						non_degraded_success = True
						i += groups[min_load]
						del groups[min_load]
						break

				# degraded merge
				if not non_degraded_success and len(groups) > 1:
					msg_execute("degraded merge process", pre=prefix)

					groups = [d for (k,d) in sorted(zip(K_merge, groups), key=lambda x: x[0], reverse=True)]
					groups[0] += groups[1]
					del groups[1]

					K_merge = [sum([dev.lambd[interface] for dev in subgroup]) for subgroup in groups]
					K_merge = [LengthAwkSlpCyl(i, DATA_TH) for i in K_merge]
					K_merge = list(map(lambda x: 2**floor(log(x, 2)), K_merge))

				elif non_degraded_success and len(groups) > 1:
					msg_execute("non-degraded merge process", pre=prefix)
				else:
					msg_warning("reamain only one group", pre=prefix)

			# record
			for i in range(len(groups)):
				# msg_execute("Group %d, wake up %d times" % (i, max(K_merge)/K_merge[i]), pre=prefix)
				for j in groups[i]:
					j.sleepCycle = K_merge[i]
					j.lbpsGroup = i
					j.wakeUpTimes = int(max(K_merge)/K_merge[i])
					j.wakeUpTimes
					# msg_execute("%s.sleepCycle = %d\t in Group %d" % (j.name, j.sleepCycle, j.lbpsGroup), pre=prefix)

			msg_success("sleep cycle length = %d with %d groups" % (max(K_merge), len(groups)), pre=prefix)
			device.sleepCycle = max(K_merge)
			return K_merge

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

LBPS_scheduling = {
	'aggr': aggr,
	'split': split,
	'merge': merge,
	'aggr-aggr': aggr_aggr
}