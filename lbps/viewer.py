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

def export_csv(performance, filename='LBPS'):
	filename = filename+".csv"
	outfile = open(filename, 'w')
	output = csv.writer(outfile)

	test_item = ['LAMBDA', 'LOAD', 'RN-PSE', 'UE-PSE',\
		'DELAY', 'PSE-FAIRNESS', 'DELAY-FAIRNESS']
	scheduling = list(sorted(performance['DELAY'].keys()))

	perform_item = ['LAMBDA', 'LOAD']
	for i in range(len(test_item)):
		if test_item[i] in perform_item:
			continue
		perform_item += [test_item[i]]
		perform_item += ['']*(len(performance[test_item[i]])-1)
	output.writerow(perform_item)

	perform_subitem = ['', '']
	for i in test_item:
		if i != 'LAMBDA' and i != 'LOAD':
			perform_subitem += list(sorted(performance[i].keys()))
	output.writerow(perform_subitem)

	for i in range(len(performance['LAMBDA'])):
		perform_value = [performance['LAMBDA'][i]]
		perform_value += [performance['LOAD'][i]]

		test_value = [performance[item][v][i] for item in test_item\
			if item != 'LAMBDA' and item != 'LOAD'\
			for v in scheduling]
		perform_value += test_value
		output.writerow(perform_value)

	outfile.close()

def export_sleep_cycle(device, sc, filename='sleep_cycle'):
	filename = filename+".csv"
	outfile = open(filename, 'w')
	output = csv.writer(outfile)

	d_list = {rn.name:[ue.name for ue in rn.childs] for rn in device.childs}
	LBPS = [i for i in sc.keys() if i != 'LAMBDA' and i != 'LOAD']

	for PS in LBPS:
		output.writerow(['LAMBDA', 'LOAD', PS])
		output.writerow(['','']+list(sorted(sc[PS]['RN'].keys())))
		for counter, k in enumerate(sc['LAMBDA']):
			rn_k = [k]
			rn_k.append(sc['LOAD'][counter])
			rn_k += [sc[PS]['RN'][i][counter] for i in list(sorted(sc[PS]['RN'].keys()))]
			output.writerow(rn_k)

		output.writerow(['LAMBDA', 'LOAD', PS])
		output.writerow(['','']+list(sorted(sc[PS]['UE'].keys())))
		for counter, k in enumerate(sc['LAMBDA']):
			ue_k = [k]
			ue_k.append(sc['LOAD'][counter])
			ue_k += [sc[PS]['UE'][i][counter] for i in list(sorted(sc[PS]['UE'].keys()))]
			output.writerow(ue_k)

	outfile.close()