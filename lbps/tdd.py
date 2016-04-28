import copy
from viewer import msg_fail, msg_warning, M3_result
from math import ceil
from config import ONE_HOP_TDD_CONFIG, TWO_HOP_TDD_CONFIG

# one hop test first
def virtual_subframe_capacity(device, interface, TDD_config):

	if device.link[interface]:
		status = device.link[interface][0].status
		real_subframe_count = len(list(filter(lambda x: x  if x == status else '', TDD_config)))
		VSC = {interface:device.capacity[interface]*real_subframe_count/len(TDD_config)}
		return VSC
	else:
		return {interface:None}

def one_to_one_first_mapping(device, interface, schedule_result, show=False):

	pre = "mapping::M3\t\t"

	try:
		status = device.link[interface][0].status
		RSC = device.capacity[interface]
		VSC = device.virtualCapacity[interface]

		real_subframe = device.tdd_config*(ceil(len(schedule_result)/len(device.tdd_config)))
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