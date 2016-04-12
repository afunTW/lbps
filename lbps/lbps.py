from poisson import getDataTH, LengthAwkSlpCyl

def aggr(device, interface):
	"""[summary] original lbps aggr scheme

	[description]

	Arguments:
		device {[list]} -- [description] a list of device
	"""
	me = type(device).__name__ + str(device.id)
	DATA_TH = getDataTH(device.buf['D'], device.link[interface][0].pkt_size)
	print("lbps::aggr::%s\t\tload= %g\t" % (me, (device.lambd[interface]/(device.capacity[interface]/device.link[interface][0].pkt_size))))
	print("lbps::aggr::%s\t\t" % me, end='')
	sleep_cycle_length = LengthAwkSlpCyl(device.lambd[interface], DATA_TH)
	print("lbps::aggr::%s\t\tsleep cycle length = %d" % (me, sleep_cycle_length))
	return sleep_cycle_length