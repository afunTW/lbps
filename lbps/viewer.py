# -*- coding: utf-8 -*-
#!/usr/bin/python3

# import matplotlib.pyplot as plt
from config import bcolors, MODE

from pprint import pprint

"""[summary] print with color tag

[description]
"""

def msg_execute(context, pre='', suf='', end='\n'):
	print(bcolors.OKBLUE + pre + context + suf + bcolors.ENDC, end=end) if MODE is "DEBUG" else print(end='')
def msg_success(context, pre='', suf='', end='\n'):
	print(bcolors.OKGREEN + pre + context + suf + bcolors.ENDC, end=end)
def msg_warning(context, pre='', suf='', end='\n'):
	print(bcolors.WARNING + pre + context + suf + bcolors.ENDC, end=end)
def msg_fail(context, pre='', suf='', end='\n'):
	print(bcolors.FAIL + pre + context + suf + bcolors.ENDC, end=end)
def msg_header(context, pre='', suf='', end='\n'):
	print(bcolors.HEADER + pre + context + suf + bcolors.ENDC, end=end)
def msg_bold(context, pre='', suf='', end='\n'):
	print(bcolors.BOLD + pre + context + suf + bcolors.ENDC, end=end)
def msg_underline(context, pre='', suf='', end='\n'):
	print(bcolors.UNDERLINE + pre + context + suf + bcolors.ENDC, end=end)

"""[summary] lbps supporting

[description]
"""

def show_sleepCycle(device, pre='', suf='', end='\n'):

	for i in device:
		if type(i) is list:
			for j in i:
				msg_execute("%s.sleepCycle = %d" % (j.name, j.sleepCycle), pre=pre, suf=suf)
		else:
			msg_execute("%s.sleepCycle = %d" % (j.name, i.sleepCycle), pre=pre, suf=suf)

def aggr_result(device, show=False):

	try:
		pre = "%s::aggr::result\t" % device.name

		device_K = device.sleepCycle
		result = []

		for i in range(device_K):
			if i % device_K is 0:
				result.append([j.name for j in device.childs])
				result[i].insert(0, device.name)
			else:
				result.append([])

		if show:
			for i in range(len(result)):
				if result[i]:
					msg_execute("subframe %d:\t%s" % (i,str(result[i])), pre=pre)

		return result

	except Exception as e:
		msg_fail(str(e), pre=pre)

def split_result(device, show=False):

	try:
		pre = "%s::split::result\t" % device.name

		result = []
		groups = {i:[] for i in range(max([g.lbpsGroup for g in device.childs])+1)}

		for i in device.childs:
			groups[i.lbpsGroup].append(i.name)

		for i in groups:
			result.append(groups[i])
			result[i].insert(0, device.name)

		if show:
			for i in range(device.sleepCycle):
				if i<len(result) and result[i]:
					suf = "Group %d:\t%s" % (i, str(result[i]))
					msg_execute("subframe %d:\t" % i, pre=pre, suf=suf)

		return result

	except Exception as e:
		msg_fail(str(e), pre=pre)

def merge_result(device, show=False):

	try:
		pre = "%s::merge::result\t" % device.name

		result = []
		groups = {i:[] for i in range(max([g.lbpsGroup for g in device.childs])+1)}
		groups_K = {i:[] for i in range(max([g.lbpsGroup for g in device.childs])+1)}
		K = {}
		queue = []

		for i in device.childs:
			groups[i.lbpsGroup].append(i.name)
			groups_K[i.lbpsGroup] = i.sleepCycle
			K.update({groups_K[i.lbpsGroup]:[]})

		for i in groups_K:
			K[groups_K[i]].append(i)

		for i in range(max(K)):

			for k in K.keys():
				queue += K[k] if i % k is 0 else []

			if queue:
				result.append(groups[queue[0]])
				result[len(result)-1].insert(0, device.name)
				del queue[0]
			else:
				result.append(None)

		if show:
			for i in range(device.sleepCycle):
				if result[i]:
					group_number = list(groups.keys())[list(groups.values()).index(result[i])]
					suf = "Group %d:\t%s" % (group_number, str(result[i]))
					msg_execute("subframe %d:\t" % i, pre=pre, suf=suf)

		return result

	except Exception as e:
		msg_fail(str(e), pre=pre)

def M3_result(device, schedule_result, map_result, show=False):

	try:
		pre = "%s::M3::result\t" % device.name

		TDD_config = device.childs[0].tdd_config if device.name[0:3] == 'eNB' else device.tdd_config
		result = { i:[] for i in range(len(schedule_result))}

		for i in range(len(map_result)):

			if map_result[i] and type(map_result[i][0]) is list:
				map_result[i] = [item for sublist in map_result[i] for item in sublist]
				map_result[i] = list(set(map_result[i]))

			if schedule_result[i] and type(schedule_result[i][0]) is list:
				schedule_result[i] = [item for sublist in schedule_result[i] for item in sublist]

			if schedule_result[i]:
				for j in map_result[i]:
					result[j] += schedule_result[i]
					result[j].insert(0, device.name)
					result[j] = list(set(result[j]))
					result[j] = sorted(result[j])

		if show:
			for i in range(len(result)):
				msg_execute("subframe %d\t[%s]:\t%s" % (i, TDD_config[i%len(TDD_config)], str(result[i])), pre=pre)

	except Exception as e:
		msg_fail(str(e), pre=pre)

def TopDown_result(device, backhaul, show=False):

	try:
		pre = "%s::TopDown::%s\t" % (device.name, backhaul)
		result = []

		# backhaul (by case)
		result = result_mapping[backhaul](device, False)

		# access (aggr)
		wakeUpTimes = [i.childs[0].wakeUpTimes for i in device.childs]
		queue = []

		while any(wakeUpTimes):
			tmp = []

			for i in range(len(wakeUpTimes)):
				if wakeUpTimes[i]:
					tmp.append([device.childs[i].name]+[j.name for j in device.childs[i].childs])
					# tmp += [j.name for j in device.childs[i].childs]
					wakeUpTimes[i] -= 1

			queue.append(tmp)

		for i in result:
			if not i and queue:
				i += queue[0]
				queue.pop(0)

		if show:
			for i in range(len(result)):
				if result[i]:
					msg_execute("subframe %d:\t%s" % (i,str(result[i])), pre=pre)

		return result

	except Exception as e:
		msg_fail(str(e), pre=pre)

result_mapping = {
	"aggr": aggr_result,
	"split": split_result,
	"merge": merge_result,
	"aggr-tdd": M3_result,
	"split-tdd": M3_result,
	"merge-tdd": M3_result,
	"aggr-aggr": TopDown_result,
	"aggr-aggr-tdd": M3_result
}