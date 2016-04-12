from poisson import getDataTH, LengthAwkSlpCyl

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
	print("lbps::aggr::%s\t\tsleep cycle length = %d" % (me, sleep_cycle_length))
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

	print("lbps::split::%s\tsleep cycle length = %d" % (me, sleep_cycle_length))