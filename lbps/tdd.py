from config import ONE_HOP_TDD_CONFIG, TWO_HOP_TDD_CONFIG
from viewer import *

# one hop test first
def virtual_subframe_capacity(device, interface, TDD_config):
	status = device.link[interface][0].status
	real_subframe_count = len(list(filter(lambda x: x  if x is status else '', TDD_config)))

	# parent
	VSC = {interface:device.capacity[interface]*real_subframe_count/len(TDD_config)}
	device.virtualCapacity = VSC

	# childs
	for i in device.childs:
		VSC = {interface:i.capacity[interface]*real_subframe_count/len(TDD_config)}
		i.virtualCapacity = VSC

	msg_success("Done", pre="TDD::VSC\t\t")