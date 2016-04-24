# -*- coding: utf-8 -*-
#!/usr/bin/python3

# import matplotlib.pyplot as plt
from config import bcolors

"""[summary] print with color tag

[description]
"""

def msg_execute(context, pre='', suf='', end='\n'):
	print(bcolors.OKBLUE + pre + context + suf + bcolors.ENDC, end=end)
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

		deivce_K = [i.sleepCycle for i in device.childs]
		result = []

		for i in range(deivce_K[0]):
			result.append([i.name for i in device.childs])

		if show:
			for i in range(len(result)):
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

		if show:
			for i in range(len(result)):
				msg_execute("subframe %d:\tGroup %d:\t%s" % (i, i, str(result[i])), pre=pre)

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
				queue += K[k] if i%(k-1) is 0 else []

			if queue:
				result.append(groups[queue[0]])
				del queue[0]
			else:
				result.append(None)

		if show:
			for i in range(len(result)):
				group_number = list(groups.keys())[list(groups.values()).index(result[i])] if result[i] else None
				suf = "Group %d:\t%s" % (group_number, str(result[i])) if group_number else "None"
				msg_execute("subframe %d:\t" % i, pre=pre, suf=suf)

		return result

	except Exception as e:
		msg_fail(str(e), pre=pre)

def M3_result(device, schedule_result, map_result, show=False):

	try:
		pre = "%s::M3::result\t\t" % device.name

		TDD_config = device.tdd_config
		result = { i:[] for i in range(len(schedule_result))}

		for i in range(len(map_result)):
			if schedule_result[i]:
				for j in map_result[i]:
					result[j] += schedule_result[i]
					result[j] = list(set(result[j]))

		if show:
			for i in range(len(result)):
				msg_execute("subframe %d\t[%s]:\t%s" % (i, TDD_config[i%len(TDD_config)], str(result[i])), pre=pre)

	except Exception as e:
		msg_fail(str(e), pre=pre)

scheduling_mapping = {
	"aggr": aggr_result,
	"split": split_result,
	"merge": merge_result
}

def scheduling_result(device, scheduling, RN=False, TDD=False, show=False):
	return scheduling_mapping[scheduling](device, show)