# -*- coding: utf-8 -*-
#!/usr/bin/python3

import matplotlib.pyplot as plt
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

	deivce_K = [i.sleepCycle for i in device.childs]
	result = []

	for i in range(deivce_K[0]):
		result.append([i.name for i in device.childs])

	if show:
		for i in range(len(result)):
			msg_execute(str(result[i]), pre="aggr::result\t\tsubframe %d\t" % i)

	return result

def split_result(device, show=False):

	result = []
	groups = {i:[] for i in range(max([g.lbpsGroup for g in device.childs])+1)}

	for i in device.childs:
		groups[i.lbpsGroup].append(i.name)

	for i in groups:
		result.append(groups[i])

	if show:
		for i in range(len(result)):
			msg_execute(str(result[i]), pre="split::result\t\tsubframe %d\tGroup %d:\t" % (i, i))

	return result

def merge_result(device, show=False):

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
			result.append(queue[0])
			del queue[0]
		else:
			result.append(None)

	if show:
		for i in range(len(result)):
			msg_execute(str(groups[result[i]]), pre="merge::result\t\tsubframe %d\tGroup %d:\t" % (i, result[i]))

	return result

scheduling_mapping = {
	"aggr": aggr_result,
	"split": split_result,
	"merge": merge_result
}

def scheduling_result(device, scheduling, RN=False, TDD=False, show=False):
	return scheduling_mapping[scheduling](device, show)