# -*- coding: utf-8 -*-
#!/usr/bin/python3

# import matplotlib.pyplot as plt
import csv
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

def export_csv(performance):
	if input("Output the performance evaluation as .csv file? (T/F)"):
		outfile = open("LBPS.csv", 'w')
		output = csv.writer(outfile)

		test_item = ['LAMBDA', 'TDD_CONFIG', 'RN-PSE', 'UE-PSE', 'DELAY']
		output.writerow(test_item)

		for i in range(len(performance['LAMBDA'])):
			test_value = [performance[j][i] for j in test_item]
			output.writerow(test_value)
		outfile.close()