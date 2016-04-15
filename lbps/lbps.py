from math import log, floor
from poisson import getDataTH, LengthAwkSlpCyl
from config import bcolors

def schedulability(check_list):
	"""[summary] check the schedulability of LBPS scheduling

	[description]

	Arguments:
		check_list {[list]} -- [description] a list of int represent the sleep cycle of list of device
	"""
	result = True if sum([1/cycle for cycle in check_list]) <= 1 else False;
	if result:
		print(bcolors.OKBLUE + "Check schedulability:\tTrue" + bcolors.ENDC)
	else:
		print(bcolors.FAIL + "Check schedulability:\tFalse" + bcolors.ENDC)
	return result

def non_degraded(device1, device2, interface, DATH_TH):
	"""[summary] check the merge process is non degraded or not

	[description]
	non degraded means the sleep cycle length is same as the original cycle length

	Arguments:
		device1 {[Device]} -- [description]
		device2 {[Device]} -- [description]
		interface {[string]} -- [description]
		DATA_TH {[int]} -- [description]
	"""
	cycle=[LengthAwkSlpCyl(d.lambd[interface], DATA_TH) for d in [device1, device2]]
	merge_sleep_cycle = LengthAwkSlpCyl(device1.lambd[interface]+device2.lambd[interface], DATA_TH)
	return True if merge_sleep_cycle in cycle else False

def aggr(device, interface):
	"""[summary] original lbps aggr scheme

	[description]
	aggrgate all UE's lambda then calculate the sleep sysle length

	Arguments:
		device {[list]} -- [description] a list of device
		interface {[string]} -- [description]
	"""
	me = type(device).__name__ + str(device.id)
	DATA_TH = getDataTH(device.buf['D'], device.link[interface][0].pkt_size)
	print("lbps::aggr::%s\t\tload= %g\t" % (me, (device.lambd[interface]/(device.capacity[interface]/device.link[interface][0].pkt_size))))
	sleep_cycle_length = LengthAwkSlpCyl(device.lambd[interface], DATA_TH)
	print(bcolors.OKGREEN + "lbps::aggr::%s\t\tsleep cycle length = %d" % (me, sleep_cycle_length) + bcolors.ENDC)
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

	# Split the group until the number of group as same as the last iterate result
	groups = []
	while len(groups) is not sleep_cycle_length and len(device.childs) > len(groups) :
		groups = [[] for i in range(sleep_cycle_length)]
		groups_load = [0 for i in range(sleep_cycle_length)]
		groups_K = [0 for i in range(sleep_cycle_length)]

		for i in range(len(device.childs)):
			min_load = groups_load.index(min(groups_load))
			groups[min_load] = device.childs[i]
			groups_load[min_load] += device.childs[i].lambd[interface]
			groups_K[min_load] = LengthAwkSlpCyl(groups_load[min_load], DATA_TH)

		sleep_cycle_length = min(groups_K) if min(groups_K) > 0 else sleep_cycle_length

	print(bcolors.OKGREEN + "lbps::split::%s\tsleep cycle length = %d with %d groups" % (me, sleep_cycle_length, len(groups)) + bcolors.ENDC)

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
	# sleep_cycle_length = LengthAwkSlpCyl(device.lambd[interface], DATA_TH)

	# one UE one group, then revise it for merge process
	K_original = [LengthAwkSlpCyl(device.childs[i].lambd[interface], DATA_TH) for i in range(len(device.childs))]
	K_star = list(map(lambda x: 2**floor(log(x, 2)), K_original))
	schedulability(K_star)