import copy
import re
from viewer import msg_fail, msg_warning, M3_result
from math import ceil
from config import ONE_HOP_TDD_CONFIG, TWO_HOP_TDD_CONFIG

"""[summary] internal support function

[description]
1. isBackhaulResult: check if a list of device name is belong to backhaul link
2. mergeList: in M3 mapping, for update the final result [pass by reference]

"""

def isBackhaulResult(devices):
	pre = "isBackhaulResult\t"

	if type(devices) is list:
		check = list(map(lambda x: re.search('eNB*', x), devices))
		return True if any(check) else False

	else:
		msg_fail("input type should be a list of device name", pre=pre)

def mergeList(target, resource):
	pre = "mergeList\t\t"

	try:

		if not target and len(resource) > len(target):
			target = resource

		elif len(target) == len(resource):
			for i in range(len(target)):

				if target[i] and resource[i]:
					msg_warning("collision", pre=pre)

				target[i] = resource[i] if not target[i] else target[i]

	except Exception as e:
		msg_fail(str(e), pre=pre)


"""[summary] external function

[description]
1. virtual_subframe_capacity: calc the virtual subframe capacity
2. one_to_one_first_mapping: M3 mapping back to real timeline

"""

def virtual_subframe_capacity(device, interface, TDD_config):

	if device.link[interface]:
		status = device.link[interface][0].status
		TDD_config = TDD_config[interface] if type(TDD_config) is dict else TDD_config
		real_subframe_count = len(list(filter(lambda x: x  if x == status else '', TDD_config)))
		VSC = {interface:device.capacity[interface]*real_subframe_count/len(TDD_config)}
		return VSC
	else:
		return {interface:None}

def one_to_one_first_mapping(device, interface, schedule_result):

	pre = "mapping::M3\t\t"

	try:
		status = device.link[interface][0].status
		RSC = device.capacity[interface]
		VSC = device.virtualCapacity[interface]

		TDD_config = device.tdd_config[interface] if type(device.tdd_config) is dict else device.tdd_config
		real_subframe = TDD_config*(ceil(len(schedule_result)/len(TDD_config)))
		real_subframe = real_subframe[:len(schedule_result)]

		mapping_to_realtimeline = [[] for i in range(len(real_subframe))]
		check_list = {i:RSC for i in range(len(real_subframe)) if real_subframe[i] is status}
		tracking_list = list(sorted(check_list.keys()))
		tracking_index = 0

		# mapping
		for i in range(len(schedule_result)):
			if check_list[tracking_list[tracking_index]] >= VSC:
				mapping_to_realtimeline[i].append(tracking_list[tracking_index])
				check_list[tracking_list[tracking_index]] -= VSC
				tracking_index = (tracking_index+1)%len(tracking_list)
				continue
			else:
				tmp = copy.deepcopy(VSC)

				while any(check_list[i] is not 0 for i in tracking_list) and tmp >0:
					mapping_to_realtimeline[i].append(tracking_list[tracking_index])
					tmp -= check_list[tracking_list[tracking_index]]
					check_list[tracking_list[tracking_index]] = 0
					tracking_index = (tracking_index+1)%len(tracking_list)
				if tmp > 0:
					msg_warning("needs more %g bits capacity" % tmp, pre=pre)

		return mapping_to_realtimeline

	except Exception as e:
		msg_fail(str(e), pre=pre)