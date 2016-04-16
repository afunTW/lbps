# -*- coding: utf-8 -*-
#!/usr/bin/python3

import matplotlib.pyplot as plt
from config import bcolors

def msg_execute(context, pre='', suf=''):
	print(bcolors.OKBLUE + pre + context + suf + bcolors.ENDC)
def msg_success(context, pre='', suf=''):
	print(bcolors.OKGREEN + pre + context + suf + bcolors.ENDC)
def msg_warning(context, pre='', suf=''):
	print(bcolors.WARNING + pre + context + suf + bcolors.ENDC)
def msg_fail(context, pre='', suf=''):
	print(bcolors.FAIL + pre + context + suf + bcolors.ENDC)
def msg_header(context, pre='', suf=''):
	print(bcolors.HEADER + pre + context + suf + bcolors.ENDC)
def msg_bold(context, pre='', suf=''):
	print(bcolors.BOLD + pre + context + suf + bcolors.ENDC)
def msg_underline(context, pre='', suf=''):
	print(bcolors.UNDERLINE + pre + context + suf + bcolors.ENDC)

def show_sleepCycle(device, pre='', suf=''):
	for i in device:
		if type(i) is list:
			for j in i:
				msg_execute("%s.sleepCycle = %d" % (type(j).__name__ + str(j.id), j.sleepCycle), pre=pre, suf=suf)
		else:
			msg_execute("%s.sleepCycle = %d" % (type(j).__name__ + str(i.id), i.sleepCycle), pre=pre, suf=suf)
