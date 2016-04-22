import copy
from math import log, floor
from poisson import getDataTH, LengthAwkSlpCyl
from config import bcolors
from viewer import *

def getLoad(device, interface, duplex="FDD"):

	try:
		capacity = device.virtualCapacity[interface] if duplex is "TDD" and device.virtualCapacity[interface] else device.capacity[interface]
		return device.lambd[interface]/(capacity/device.link[interface][0].pkt_size)

	except Exception as e:
		msg_fail(str(e), pre="%s::getLoad\t\t" % device.name)
		return

def getCapacity(device, interface, duplex):

	try:
		duplex = duplex.upper() if type(duplex) is str else ""

		if duplex == 'FDD':
			return device.capacity[interface]
		elif duplex == 'TDD' and device.virtualCapacity[interface]:
			return device.virtualCapacity[interface]
		else:
			return 0

	except Exception as e:
		msg_fail(str(e), pre="%s::getCapacity\t\t" % device.name)

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

def aggr(device, interface, duplex='FDD'):

	prefix = "lbps::aggr::%s\t\t" % device.name

	try:

		capacity = getCapacity(device, interface, duplex)
		DATA_TH = getDataTH(capacity, device.link[interface][0].pkt_size)
		msg_success("load= %g\t" % getLoad(device, interface), pre=prefix)

		# aggr process
		sleep_cycle_length = LengthAwkSlpCyl(device.lambd[interface], DATA_TH)

		# record
		for i in device.childs:
			i.sleepCycle = sleep_cycle_length
			msg_execute("%s.sleepCycle = %d" % (i.name, i.sleepCycle), pre=prefix)

		device.sleepCycle = sleep_cycle_length
		msg_success("sleepCycle = %d" % i.sleepCycle ,pre=prefix)
		return sleep_cycle_length

	except Exception as e:
		msg_fail(str(e), pre=prefix)
		return

def split(device, interface, duplex='FDD'):

	prefix = "lbps::split::%s\t" % device.name

	try:
		# init
		capacity = getCapacity(device, interface, duplex)
		DATA_TH = getDataTH(capacity, device.link[interface][0].pkt_size)
		msg_success("load= %g\t" % getLoad(device, interface), pre=prefix)

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
				# msg_execute("%s.sleepCycle = %d\tin Group %d" % (j.name, j.sleepCycle, j.lbpsGroup), pre=prefix)

		device.sleepCycle = sleep_cycle_length
		msg_success("sleep cycle length = %d with %d groups" % (sleep_cycle_length, len(groups)), pre=prefix)
		return sleep_cycle_length

	except Exception as e:
		msg_fail(str(e), pre=prefix)
		return

def merge(device, interface, duplex='FDD'):

	prefix = "lbps::merge::%s\t" % device.name

	try:
		# init
		capacity = getCapacity(device, interface, duplex)
		DATA_TH = getDataTH(capacity, device.link[interface][0].pkt_size)
		print(prefix + "load= %g\t" % getLoad(device, interface))

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
			msg_success("Group %d, wake up %d times" % (i, max(K_merge)/K_merge[i]), pre=prefix)
			for j in groups[i]:
				j.sleepCycle = K_merge[i]
				j.lbpsGroup = i
				# msg_execute("%s.sleepCycle = %d\t in Group %d" % (j.name, j.sleepCycle, j.lbpsGroup), pre=prefix)

		device.sleepCycle = max(K_merge)
		msg_success("sleep cycle length = %d with %d groups" % (max(K_merge), len(groups)), pre=prefix)
		return K_merge

	except Exception as e:
		msg_fail(str(e), pre=prefix)
		return