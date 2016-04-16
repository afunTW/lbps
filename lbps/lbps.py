import copy
from math import log, floor
from poisson import getDataTH, LengthAwkSlpCyl
from config import bcolors

def schedulability(check_list):
	result = True if sum([1/cycle for cycle in check_list]) <= 1 else False;
	if result:
		print(bcolors.OKBLUE + "Check schedulability:\tTrue" + bcolors.ENDC)
	else:
		print(bcolors.FAIL + "Check schedulability:\tFalse" + bcolors.ENDC)
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

def aggr(device, interface):
	"""[summary] original lbps aggr scheme

	[description]
	aggrgate all UE's lambda then calculate the sleep sysle length
	assign the sleep cycle length to each UE at the end

	Arguments:
		device {[list]} -- [description] a list of device
		interface {[string]} -- [description]
	"""

	me = type(device).__name__ + str(device.id)
	DATA_TH = getDataTH(device.buf['D'], device.link[interface][0].pkt_size)
	print("lbps::aggr::%s\t\tload= %g\t" % (me, (device.lambd[interface]/(device.capacity[interface]/device.link[interface][0].pkt_size))))

	sleep_cycle_length = LengthAwkSlpCyl(device.lambd[interface], DATA_TH)
	for i in device.childs:
		i.sleepCycle = sleep_cycle_length
		# print(bcolors.OKBLUE + "lbps::aggr::%s\t\t%s.sleepCycle = %d" % (me, type(i).__name__ + str(i.id), i.sleepCycle) + bcolors.ENDC)

	device.sleepCycle = sleep_cycle_length
	print(bcolors.OKGREEN + "lbps::aggr::%s\t\tsleepCycle = %d" % (me, i.sleepCycle) + bcolors.ENDC)
	return sleep_cycle_length

def split(device, interface):
	"""[summary] original lbps split scheme

	[description]
	split the group in the length of sleep cycle

	Arguments:
		device {[list]} -- [description] a list of device
		interface {[string]} -- [description]
	"""

	me = type(device).__name__ + str(device.id)
	DATA_TH = getDataTH(device.buf['D'], device.link[interface][0].pkt_size)
	print("lbps::split::%s\tload= %g\t" % (me, (device.lambd[interface]/(device.capacity[interface]/device.link[interface][0].pkt_size))))

	sleep_cycle_length = LengthAwkSlpCyl(device.lambd[interface], DATA_TH)
	groups = [copy.deepcopy(device.childs)]
	old_groupsLength = 0

	# Split the group until the number of group as same as the last iterate result
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

	for i in range(len(groups)):
		for j in groups[i]:
			j.sleepCycle = groups_K[i]
			# print(bcolors.OKBLUE + "lbps::split::%s\t%s.sleepCycle = %d" % (me, type(j).__name__ + str(j.id), j.sleepCycle) + bcolors.ENDC)

	print(bcolors.OKGREEN + "lbps::split::%s\tsleep cycle length = %d with %d groups" % (me, sleep_cycle_length, len(groups)) + bcolors.ENDC)
	return sleep_cycle_length

def merge(device, interface):
	"""[summary] original lbps merge scheme

	[description]

	Arguments:
		device {[list]} -- [description] a list of device
		interface {[string]} -- [description] 'access' or 'backhaul'
	"""

	me = type(device).__name__ + str(device.id)
	DATA_TH = getDataTH(device.buf['D'], device.link[interface][0].pkt_size)
	print("lbps::merge::%s\tload= %g\t" % (me, (device.lambd[interface]/(device.capacity[interface]/device.link[interface][0].pkt_size))))

	groups = [[i] for i in device.childs]
	groups_load = [i.lambd[interface] for i in device.childs]
	K_original = [LengthAwkSlpCyl(device.childs[i].lambd[interface], DATA_TH) for i in range(len(device.childs))]
	K_merge = list(map(lambda x: 2**floor(log(x, 2)), K_original))

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
		if not non_degraded_success:
			max_K_groups = [d for (k,d) in sorted(zip(K_merge, groups), key=lambda x: x[0], reverse=True)]
			max_K_1 = groups.index(max_K_groups[0])
			max_K_2 = groups.index(max_K_groups[1])
			groups[max_K_1] += groups[max_K_2]
			del groups[max_K_2]

		break