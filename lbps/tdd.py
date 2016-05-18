import copy
import re
from viewer import msg_fail, msg_warning
from math import ceil
from config import *
from pprint import pprint

"""[summary] internal support function

[description]
1. isBackhaulResult: check if a list of device name is belong to backhaul link
2. mergeList: in M3 mapping, for update the final result [pass by reference]

"""

def isBackhaulResult(devices):
	pre = "isBackhaulResult\t"

	if not devices:
		# msg_warning("input value is an empty list", pre=pre)
		return

	if type(devices) is list:
		devices = [item for sublist in devices for item in sublist] if type(devices[0]) is list else devices
		check = list(map(lambda x: re.search('UE*', x), devices))
		return True if not any(check) else False

	else:
		msg_fail("input type should be a list of device name", pre=pre)

def filterByInterface(schedule_result, map_result, interface):
	pre = "filterByInterface\t"

	try:
		check = list(map(lambda x: isBackhaulResult(x), schedule_result))

		for i in range(len(schedule_result)):

			if interface == 'backhaul':
				map_result[i] = map_result[i] if check[i] else []
			else:
				map_result[i] = map_result[i] if not check[i] else []

	except Exception as e:
		msg_fail(str(e), pre=pre)

def mergeList(target, resource):
	pre = "mergeList\t\t"

	try:

		# init
		if not target and len(resource) > len(target):
			target = resource

		elif len(target) == len(resource):
			for i in range(len(resource)):
				target[i].append(resource[i]) if resource[i] else target[i]

		return target

	except Exception as e:
		msg_fail(str(e), pre=pre)

"""[summary] external function

[description]
1. continuous mapping
2. one_to_one_first_mapping

"""

def continuous_mapping(TDD_config, detail=False):
	pre = "mapping::M2\t\t"

	try:
		RSC = 10
		VSC = TDD_config.count('D')*RSC/10
		v_timeline = [{'r_TTI': [], 'VSC': VSC} for i in range(10)]
		config = copy.deepcopy(TDD_config)
		config = [{'r_TTI': i, 'RSC': RSC} for i in range(10) if config[i] is 'D']

		for vs in v_timeline:
			for rs in config:
				if rs['RSC'] > vs['VSC']:
					rs['RSC'] -= vs['VSC']
					vs['VSC'] = 0
					vs['r_TTI'].append(rs['r_TTI'])
					break
				elif rs['RSC']:
					vs['VSC'] -= rs['RSC']
					rs['RSC'] = 0
					vs['r_TTI'].append(rs['r_TTI'])

		return v_timeline if detail else [i['r_TTI'] for i in v_timeline]

	except Exception as e:
		msg_fail(str(e), pre=pre)

def one_to_one_first_mapping(TDD_config, detail=False):

	pre = "mapping::M3\t\t"

	try:
		RSC = 10
		VSC = TDD_config.count('D')*RSC/10
		v_timeline = [{'r_TTI':[], 'VSC':VSC} for i in range(10)]
		track_index = 0
		config = copy.deepcopy(TDD_config)
		config = [{'r_TTI': i, 'RSC': RSC} for i in range(10) if config[i] is 'D']

		# mapping
		for i in range(len(v_timeline)):

			if config[track_index]['RSC'] >= v_timeline[i]['VSC']:
				config[track_index]['RSC'] -= v_timeline[i]['VSC']
				v_timeline[i]['VSC'] = 0
				v_timeline[i]['r_TTI'].append(config[track_index]['r_TTI'])
				track_index = (track_index+1)%len(config)
				continue

			for j in [(track_index+t)%len(config) for t in range(len(config))]:
				if v_timeline[i]['VSC'] == 0:
					break
				if config[j]['RSC'] == 0:
					continue

				v_timeline[i]['r_TTI'].append(config[j]['r_TTI'])

				if config[j]['RSC']<=v_timeline[i]['VSC']:
					v_timeline[i]['VSC'] -= config[j]['RSC']
					config[j]['RSC'] = 0
				else :
					config[j]['RSC'] -= v_timeline[i]['VSC']
					v_timeline[i]['VSC'] =0

			track_index = (track_index+1)%len(config)

		return v_timeline if detail else [i['r_TTI'] for i in v_timeline]

	except Exception as e:
		msg_fail(str(e), pre=pre)

def two_hop_one_to_one_first_mapping(TDD_config, detail=False):

	pre = "mapping::2hopM3\t\t"

	try:
		if not is_backhaul_config(TDD_config):
			raise Exception("only accept backhaul TDD configuration as input")

		# init
		backhaul_config = copy.deepcopy(TDD_config)
		access_config = get_access_by_backhaul_config(backhaul_config, no_backhaul=True)
		RSC = 10
		VSC = (backhaul_config.count('D')+access_config.count('D'))*RSC/10
		v_timeline = [{'r_TTI':[], 'VSC':VSC, 'identity':[]} for i in range(10)]
		r_config = [
			{'r_TTI':i, 'RSC': RSC, 'identity': 'backhaul'} for i in range(10)
			if backhaul_config[i] == 'D']
		r_config += [
			{'r_TTI':i, 'RSC': RSC, 'identity': 'access'} for i in range(10)
			if access_config[i] == 'D']
		r_index = 0

		# mapping
		for i in range(len(v_timeline)):
			if r_config[r_index]['RSC'] >= v_timeline[i]['VSC']:
				r_config[r_index]['RSC'] -= v_timeline[i]['VSC']
				v_timeline[i]['r_TTI'].append(r_config[r_index]['r_TTI'])
				v_timeline[i]['identity'].append(r_config[r_index]['identity'])
				v_timeline[i]['VSC'] = 0
				r_index = (r_index+1)%len(r_config)
				continue
			for j in [(r_index+t)%len(r_config) for t in range(len(r_config))]:
				if v_timeline[i]['VSC'] == 0:
					break
				if r_config[j]['RSC'] == 0:
					continue
				if r_config[j]['RSC'] >= v_timeline[i]['VSC']:
					r_config[j]['RSC'] -= v_timeline[i]['VSC']
					v_timeline[i]['VSC'] = 0
				else:
					v_timeline[i]['VSC'] -= r_config[j]['RSC']
					r_config[j]['RSC'] = 0

				v_timeline[i]['r_TTI'].append(r_config[j]['r_TTI'])
				v_timeline[i]['identity'].append(r_config[j]['identity'])
				v_timeline[i]['identity'] = list(set(v_timeline[i]['identity']))

		return [i['r_TTI'] for i in v_timeline] if not detail else v_timeline

	except Exception as e:
		msg_fail(str(e), pre=pre)


if __name__ == '__main__':
	print(one_to_one_first_mapping(ONE_HOP_TDD_CONFIG[1]))