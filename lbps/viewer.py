# -*- coding: utf-8 -*-
#!/usr/bin/python3

import matplotlib.pyplot as plt
from config import bcolors

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

def show_sleepCycle(device, pre='', suf='', end='\n'):
	for i in device:
		if type(i) is list:
			for j in i:
				msg_execute("%s.sleepCycle = %d" % (j.name, j.sleepCycle), pre=pre, suf=suf)
		else:
			msg_execute("%s.sleepCycle = %d" % (j.name, i.sleepCycle), pre=pre, suf=suf)

def show_aggr_result(device, show=False):
	deivce_K = [i.sleepCycle for i in device.childs]
	result = []

	for i in range(deivce_K[0]):
		result.append([i.name for i in device.childs])

	if show:
		for i in range(len(result)):
			msg_execute("aggr::result\t\tsubframe %d\t" % i)
			for j in range(len(result[i])):
				pre = '\t\t\t' if (j+1) % 5 is 1 else '\t'
				end = '\n' if (j+1) % 5 is 0 else '\t'
				msg_execute(result[i][j], pre=pre, end=end)

	return result

# def show_split_result(device, show=False):
	# getGroup

# def show_scheduling_result(device, scheduling, RN=False, TDD=False):
# 	show = {
# 		"aggr":

# 	}