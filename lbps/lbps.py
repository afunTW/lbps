import random
import copy
import re
from math import log, floor, ceil
from tdd import continuous_mapping as M2
from tdd import two_hop_mapping as m_2hop
from device import UE, RN, eNB

from poisson import getDataTH, LengthAwkSlpCyl, DataAcc
from config import *
from viewer import *
from pprint import pprint

"""[summary] internal function

[description] abstract level of lbps
"""

def getLoad(device, duplex="FDD"):

	try:
		interface = 'backhaul' if isinstance(device, eNB) else 'access'
		capacity = device.capacity if duplex == 'FDD' else device.virtualCapacity
		capacity = capacity[interface] if type(capacity) is dict else capacity
		return device.lambd[interface]*getAvgPktSize(device)/capacity

	except Exception as e:
		msg_fail(str(e), pre="%s::getLoad\t\t" % device.name)

def getAvgPktSize(device):
	interface = 'backhaul' if isinstance(device, eNB) else 'access'
	total_pkt = [bearer.flow for bearer in device.link[interface]]
	total_pkt = [traffic[i]['pkt_size'] for i in total_pkt]
	return sum(total_pkt)/len(total_pkt)

def getDeviceByName(device, name_list):
	result = []
	d = {
		'eNB':device,
		'RN':[rn for rn in device.childs],
		'UE':[ue for rn in device.childs for ue in rn.childs]
	}

	for i in name_list:
		if re.search('eNB*', i):
			result.append(device)
		elif re.search('RN*', i):
			for rn in d['RN']:
				if rn.name == i:
					result.append(rn)
					break
		elif re.search('UE*', i):
			for ue in d['UE']:
				if ue.name == i:
					result.append(ue)
					break
	return result

def schedulability(check_list):

	result = True if sum([1/cycle for cycle in check_list]) <= 1 else False;
	# result and msg_success("Check schedulability:\tTrue")
	# not result and msg_warning("Check schedulability:\tFalse")

	return result

def non_degraded(G, interface, DATA_TH):

	if len(G) is 1:
		return G

	source_G = G.pop(0)
	result = False

	for i in G:
		new_K = LengthAwkSlpCyl(source_G['lambda']+i['lambda'], DATA_TH)
		new_K = 2**floor(log(new_K, 2))
		if new_K == i['K']:
			result = True
			i['device'] += source_G['device']
			i['lambda'] += source_G['lambda']
			break

	not result and G.append(source_G)
	G.sort(key=lambda x: x['K'], reverse=True)

	return G

def access_aggr(device, b_result):

	if b_result:
		lbps_failed = []

		for rn in device.childs:
			b_TTI = None
			a_subframe = ceil(device.virtualCapacity/rn.virtualCapacity)

			if a_subframe > len(b_result)-1:
				lbps_failed.append(rn)
				continue

			for i in b_result:
				if a_subframe == 0:
					break
				if rn in i:
					continue
				i += rn.childs
				i.append(rn)
				a_subframe -= 1

		return lbps_failed

	return

def two_hop_realtimeline(mapping_pattern, t, b, a):
	k = len(a)

	# extend and align timeline
	b_lbps_result = b*ceil(t/len(b))
	b_lbps_result = b_lbps_result[:t]
	a_lbps_result = a*ceil(t/len(a))
	a_lbps_result = a_lbps_result[:t]
	timeline = {'backhaul':[[] for i in range(t)], 'access':[[] for i in range(t)]}
	vt_mapping = {'backhaul':[], 'access':[]}

	for i in range(ceil(t/10)):
		vt_mapping['backhaul'] += [[i*10+v for v in su] for su in mapping_pattern['backhaul']]
		vt_mapping['access'] += [{
			'identity':su['identity'],
			'TTI': [i*10+v for v in su['r_TTI']]} for su in mapping_pattern['access']]

	# backhaul mapping
	for i in range(t):
		for rsb in vt_mapping['backhaul'][i]:
			timeline['backhaul'][rsb] += b_lbps_result[i]

	# access mapping
	for i in range(0, t-k, k):
		tmp_map = {'access':[], 'mixed':[], 'backhaul':[]}
		for j in vt_mapping['access'][i:i+k]:
			tmp_map[j['identity']].append(j)

		for vt in a_lbps_result[i:i+k]:
			if not vt:
				continue

			identity = 'backhaul' if tmp_map['backhaul'] else None
			identity = 'mixed' if tmp_map['mixed'] else identity
			identity = 'access' if tmp_map['access'] else identity

			for rsb in tmp_map[identity][0]['TTI']:
				timeline['access'][rsb] += vt

			tmp_map[identity].pop(0)

	for i in range(len(timeline['backhaul'])):
		timeline['backhaul'][i] = list(set(timeline['backhaul'][i]))
		timeline['access'][i] = list(set(timeline['access'][i]))

	return timeline

def check_mincycle(device, rn_status, b_min_cycle):
	for rn in device.childs:
		rate = rn.virtualCapacity/device.virtualCapacity

		if len(rn_status[rn.name]['result']) > b_min_cycle:
			pkt_size = getAvgPktSize(rn)
			DATA_TH = int(getDataTH(rn.virtualCapacity, pkt_size))
			accumulate_K = LengthAwkSlpCyl(rn.lambd['access'], DATA_TH, PROB_TH=0.2)
			accumulate_pkt = DataAcc(rn.lambd['access'], b_min_cycle)

			if not accumulate_pkt:
				result = aggr(rn, 'TDD')
				a_count = sum([1 for i in result if i])
				rn_status[rn.name].update({
					'result':result,
					'a-availability':True,
					'a-subframe-count': a_count,
					'b-subframe-count': a_count*rate})
			else:
				a_count = ceil(accumulate_pkt*pkt_size/rn.virtualCapacity)
				rn_status[rn.name].update({
					'a-availability':True,
					'a-subframe-count':a_count,
					'b-subframe-count':ceil(a_count*rate)
				})

			if rn_status[rn.name]['a-subframe-count']\
			+rn_status[rn.name]['b-subframe-count']\
			>b_min_cycle:
				rn_status[rn.name]['a-availability'] = False
		else:
			a_count = sum([1 for i in rn_status[rn.name]['result'] if i])
			rn_status[rn.name].update({
				'a-availability':True,
				'a-subframe-count':a_count,
				'b-subframe-count':ceil(a_count*rate)})

def allocate_mincycle_backhaul(device, rn_status, b_min_cycle):
	b_lbps_result = [[] for i in range(b_min_cycle)]
	for (rn, info) in rn_status.items():
		for TTI in range(b_min_cycle):
			if not b_lbps_result[TTI]\
			and info['b-subframe-count']\
			and TTI+info['b-subframe-count']<b_min_cycle:
				b_lbps_result[TTI:TTI+info['b-subframe-count']]\
				=[[device, info['device']]]*info['b-subframe-count']
				rn_status[rn]['b-availability'] = True
				break
		if not rn_status[rn]['b-availability']:
			b_lbps_result = [ i+[device, info['device']] for i in b_lbps_result]
	return b_lbps_result

def allocate_mincycle_access(rn_status, b_min_cycle):
	a_lbps_result = [[] for i in range(b_min_cycle)]
	for (rn, info) in rn_status.items():
		if info['a-availability']:
			# # for min-split case when required subframe means number of groups
			# if info['a-subframe-count']>=b_min_cycle:
			# 	pkt_size = getAvgPktSize(info['device'])
			# 	lambd = info['device'].lambd['access']
			# 	info['a-subframe-count'] = ceil(DataAcc(lambd, b_min_cycle)*pkt_size/info['device'].virtualCapacity)

			for i in range(info['a-subframe-count']):
				a_lbps_result[i] += info['result'][i] if info['result'][i] else []
		else:
			a_lbps_result = [i+[info['device']]+info['device'].childs for i in a_lbps_result]
	return a_lbps_result

def get_sleep_cycle(device, b_lbps_result, a_lbps_result):
	return {
		'RN':{rn.name:\
			[len(b_lbps_result)/sum([1 for TTI in b_lbps_result if rn in TTI])]\
			for rn in device.childs},
		'UE':{ue.name:\
			[len(a_lbps_result)/sum([1 for TTI in a_lbps_result if ue in TTI ])]\
			for rn in device.childs for ue in rn.childs}
	}

"""[summary] original lbps algorithm

[description] for one-hop in FDD
"""

def aggr(device, duplex='FDD'):

	prefix = "lbps::aggr::%s \t" % device.name

	try:
		# duplex will only affect the capacity, not related to mapping
		if duplex is not 'FDD' and duplex is not 'TDD':
			return

		if not isinstance(device, eNB) and not isinstance(device, RN):
			return

		interface = 'backhaul' if isinstance(device, eNB) else 'access'
		capacity = device.capacity if duplex == 'FDD' else device.virtualCapacity
		capacity = capacity[interface] if type(capacity) is dict else capacity
		pkt_size = getAvgPktSize(device)
		DATA_TH = int(getDataTH(capacity, pkt_size))
		msg_execute("load= %g\t" % getLoad(device, duplex), pre=prefix)

		# aggr process
		sleep_cycle_length = LengthAwkSlpCyl(device.lambd[interface], DATA_TH)
		msg_execute("sleepCycle = %d" % sleep_cycle_length ,pre=prefix)

		result = [[] for i in range(sleep_cycle_length)]
		result[0] = [i for i in device.childs]
		result[0].append(device)
		result[0] = sorted(result[0], key=lambda d: d.name)

		return result

	except Exception as e:
		msg_fail(str(e), pre=prefix)
		return

def split(device, duplex='FDD', boundary_group=None):

	prefix = "lbps::split::%s\t" % device.name

	try:
		# duplex will only affect the capacity, not related to mapping
		if duplex is not 'FDD' and duplex is not 'TDD':
			return

		if not isinstance(device, eNB) and not isinstance(device, RN):
			return

		interface = 'backhaul' if isinstance(device, eNB) else 'access'
		capacity = device.capacity if duplex == 'FDD' else device.virtualCapacity
		capacity = capacity[interface] if type(capacity) is dict else capacity
		pkt_size = getAvgPktSize(device)
		DATA_TH = int(getDataTH(capacity, pkt_size))
		msg_execute("load= %g\t" % getLoad(device, duplex), pre=prefix)
		sleep_cycle_length = LengthAwkSlpCyl(device.lambd[interface], DATA_TH)

		groups = {
			0: {
				'device': [ch for ch in device.childs],
				'lambda': device.lambd[interface],
				'K': sleep_cycle_length
			}
		}

		if not boundary_group or boundary_group > len(device.childs):
			boundary_group = len(device.childs)

		# Split process
		while len(groups) < sleep_cycle_length:
			groups = {
				i:{
					'device': [],
					'lambda':0,
					'K': 0
				}
				for i in range(min(sleep_cycle_length, boundary_group))
			}

			for i in device.childs:

				# find the minimum lambda group
				min_lambd = min([groups[G]['lambda'] for G in groups])
				min_lambd_G = [G for G in groups if groups[G]['lambda'] == min_lambd]
				min_lambd_G = random.choice(min_lambd_G)

				# append the device to the minimum lambda group
				# FIXME: performance issue
				groups[min_lambd_G]['device'].append(i)
				groups[min_lambd_G]['lambda'] += i.lambd[interface]
				groups[min_lambd_G]['K'] = LengthAwkSlpCyl(groups[min_lambd_G]['lambda'], DATA_TH)

			K = min([groups[G]['K'] for G in groups])

			if K == sleep_cycle_length:
				break
			elif len(groups) == boundary_group:
				sleep_cycle_length = K if K > 0 else sleep_cycle_length
				break
			else:
				sleep_cycle_length = K if K > 0 else sleep_cycle_length

		msg_execute("sleep cycle length = %d with %d groups" % \
			(sleep_cycle_length, len(groups)), pre=prefix)

		result = [[] for i in range(sleep_cycle_length)]
		for i in groups:
			groups[i]['device'] and groups[i]['device'].append(device)
			result[i] += groups[i]['device']

		return result

	except Exception as e:
		msg_fail(str(e), pre=prefix)
		return

def merge(device, duplex='FDD', two_hop=False):

	prefix = "lbps::merge::%s\t" % device.name

	try:
		# duplex will only affect the capacity, not related to mapping
		if duplex is not 'FDD' and duplex is not 'TDD':
			return

		if not isinstance(device, eNB) and not isinstance(device, RN):
			return

		interface = 'backhaul' if isinstance(device, eNB) else 'access'
		capacity = device.capacity if duplex == 'FDD' else device.virtualCapacity
		capacity = capacity[interface] if type(capacity) is dict else capacity
		pkt_size = getAvgPktSize(device)
		DATA_TH = int(getDataTH(capacity, pkt_size))
		msg_execute("load= %g\t" % getLoad(device, duplex), pre=prefix)
		required_backhaul_subframe = None

		# init merge groups
		groups = [
			{
				'device': [i],
				'lambda': i.lambd[interface],
				'K': 2**floor(log(LengthAwkSlpCyl(i.lambd[interface], DATA_TH), 2))
			} for i in device.childs
		]

		# merge process
		while True:
			check_list = [i['K'] for i in groups]

			if two_hop:
				Ki = max([G['K'] for G in groups])
				required_access_subframe = int(sum([Ki/G['K'] for G in groups]))
				required_backhaul_subframe = ceil(DATA_TH*required_access_subframe*pkt_size/device.virtualCapacity)
				if sum([1/KG for KG in check_list])+(required_backhaul_subframe/Ki)<=1:
					break

			elif schedulability(check_list):
				break

			# non-degraded merge
			groups.sort(key=lambda x: x['K'], reverse=True)
			g_non_degraded = non_degraded(groups, interface, DATA_TH)
			non_degraded_success = False if len(g_non_degraded) == len(groups) else True
			groups = g_non_degraded

			# degraded merge
			if not non_degraded_success and len(groups) > 1:
				groups[1]['device'] += groups[0]['device']
				groups[1]['lambda'] += groups[0]['lambda']
				groups[1]['K'] = LengthAwkSlpCyl(groups[1]['lambda'], DATA_TH)
				groups.pop(0)

		# calc the times of waking up for group
		max_K = max([G['K'] for G in groups])
		groups.sort(key=lambda x: x['K'])

		msg_execute("sleep cycle length = %d with %d groups" % \
				(max_K, len(groups)), pre=prefix)

		result = {i:[] for i in range(max_K)}

		for G in groups:
			base = 0
			for i in list(result.keys()):
				if not result[i]:
					base = i
					break
			for TTI in range(base, len(result), G['K']):
				result[TTI] = G['device'] + [device]

		a_result = list(result.values())

		if two_hop:
			b_result = [[device, device.parent]]*required_backhaul_subframe
			b_result.extend([[]]*(max_K-required_backhaul_subframe))
			return {'backhaul':b_result, 'access':a_result}

		return a_result

	except Exception as e:
		msg_fail(str(e), pre=prefix)
		return

"""[summary] proposed lbps algorithm

[description] for two hop in TDD with multiple RN and considering different CQI
"""

def min_aggr(device, simulation_time, check_K=False):
	prefix = "BottomUp::min-aggr\t"
	duplex = 'TDD'

	try:
		rn_status = {
			rn.name:{
				'device':rn,
				'result':aggr(rn, duplex),
				'a-availability':False,
				'b-availability':False,
				'a-subframe-count':None,
				'b-subframe-count': None
			} for rn in device.childs
		}

		# minCycle availability check
		b_min_cycle = min([len(rn_status[i]['result']) for i in rn_status])
		check_mincycle(device, rn_status, b_min_cycle)

		# backhaul scheduling and scheduliability check
		b_lbps_result = allocate_mincycle_backhaul(device, rn_status, b_min_cycle)

		# access scheduling and scheduliability check
		a_lbps_result = allocate_mincycle_access(rn_status, b_min_cycle)

		msg_warning("access K= %d\t\tN_a= %d\tN_Bh= %d"%\
			(len(a_lbps_result),\
				rn_status[device.childs[0].name]['a-subframe-count'],\
				rn_status[device.childs[0].name]['b-subframe-count']),\
			pre=prefix)

		mapping_pattern = m_2hop(device.tdd_config)
		timeline = two_hop_realtimeline(
			mapping_pattern,
			simulation_time,
			b_lbps_result,
			a_lbps_result)

		msg_warning("total awake: %d times" %\
			(sum([1 for i in timeline['backhaul'] if i])+\
			sum([1 for i in timeline['access'] if i])-\
			sum([1 for i in range(len(timeline['access'])) \
				if timeline['backhaul'][i] and timeline['access'][i]]
		)), pre=prefix)

		if check_K:
			return get_sleep_cycle(device, b_lbps_result, a_lbps_result)

		return timeline

	except Exception as e:
		msg_fail(str(e), pre=prefix)

def min_split(device, simulation_time, check_K=False):
	prefix = "BottomUp::min-split\t"
	duplex = 'TDD'

	try:
		rn_status = {
			rn.name:{
				'device':rn,
				'result':split(rn, duplex),
				'a-availability':False,
				'b-availability':False,
				'a-subframe-count':None,
				'b-subframe-count': None
			} for rn in device.childs
		}

		# minCycle availability check
		b_min_cycle = min([len(rn_status[i]['result']) for i in rn_status])
		check_mincycle(device, rn_status, b_min_cycle)

		for (rn_name, info) in rn_status.items():
			boundary_group = len(info['device'].childs)

			while not info['a-availability'] and boundary_group>1:
				boundary_group -= 1
				info['result'].update(split(info['device'], duplex, boundary_group))
				check_mincycle(device, rn_status, b_min_cycle)

		# backhaul scheduling and scheduliability check
		b_lbps_result = allocate_mincycle_backhaul(device, rn_status, b_min_cycle)

		# access scheduling and scheduliability check
		a_lbps_result = allocate_mincycle_access(rn_status, b_min_cycle)

		msg_warning("access K= %d\t\tN_a= %d\tN_Bh= %d"%\
			(len(a_lbps_result),\
				rn_status[device.childs[0].name]['a-subframe-count'],\
				rn_status[device.childs[0].name]['b-subframe-count']),\
			pre=prefix)

		mapping_pattern = m_2hop(device.tdd_config)
		timeline = two_hop_realtimeline(
			mapping_pattern,
			simulation_time,
			b_lbps_result,
			a_lbps_result)

		msg_warning("total awake: %d times" %\
			(sum([1 for i in timeline['backhaul'] if i])+\
			sum([1 for i in timeline['access'] if i])-\
			sum([1 for i in range(len(timeline['access'])) \
				if timeline['backhaul'][i] and timeline['access'][i]]
		)), pre=prefix)

		if check_K:
			return get_sleep_cycle(device, b_lbps_result, a_lbps_result)

		return timeline

	except Exception as e:
		msg_fail(str(e), pre=prefix)

def merge_merge(device, simulation_time, check_K=False):
	prefix = "BottomUp::merge-merge\t"
	duplex = 'TDD'

	try:
		rn_status = {
			rn.name:{
				'device':rn,
				'result':merge(rn, duplex, two_hop=True),
				'a-subframe-count':None,
				'b-subframe-count': None,
				'access-failed':False
			} for rn in device.childs
		}
		a_lbps_result = [[]\
			for i in range(max([len(K['result']['access'])\
			for K in rn_status.values()]))]
		b_lbps_result = []

		# considering the case of difference link quality
		for (rn_name, info) in rn_status.items():
			info['a-subframe-count'] = sum([1 for i in info['result']['access'] if i])
			info['b-subframe-count'] = ceil(\
				info['a-subframe-count']*\
				info['device'].virtualCapacity/\
				device.virtualCapacity)

			access_K = len(info['result']['access'])

			# check access schedulability
			if info['a-subframe-count']+info['b-subframe-count']>access_K:
				info['access-failed']=True
				msg_fail("%s access schedulability failed" % rn_name, pre=prefix)

			for i,v in enumerate(info['result']['access']):
				a_lbps_result[i] += v

		# check access schedulability
		backhaul_failed = False
		if any([rn_v['access-failed'] for rn_v in rn_status.values()]):
			msg_fail("access schedulability failed", pre=prefix)
			b_lbps_result = [[rn for rn in device.childs]]*len(a_lbps_result)
		else:
			# backhaul merge process (non-degraded only)
			groups = [
				{
					'device': [i],
					'K': len(rn_status[i.name]['result']['access']),
					'N_Bh': rn_status[i.name]['b-subframe-count']
				} for i in device.childs
			]

			while sum([ceil(i['N_Bh'])/i['K'] for i in groups]) > 1:
				msg_warning("backhaul schedulability failed", pre=prefix)

				groups.sort(key=lambda x:x['K'], reverse=True)
				non_degraded_success = False
				for source_G in groups:
					for target_G in groups:
						if target_G is not source_G\
						and target_G['K'] == source_G['K']\
						and ceil(target_G['N_Bh']+source_G['N_Bh'])<source_G['K']:
							non_degraded_success=True
							source_G['device'] += target_G['device']
							source_G['N_Bh'] += target_G['N_Bh']
							groups.remove(target_G)
							break
					else: continue
					break

				if not non_degraded_success:
					backhaul_failed=True
					break

			# check backhaul schedulability
			if backhaul_failed:
				b_lbps_result = [[rn for rn in device.childs]]*len(a_lbps_result)
				msg_fail("backhaul schedulability failed", pre=prefix)
			else:
				# calc the times of waking up for group
				max_K = max([G['K'] for G in groups])
				msg_execute("sleep cycle length = %d with %d groups" % \
						(max_K, len(groups)), pre=prefix)

				b_lbps_result = []
				for G in groups:
					G['device'] += [device]
					G['device'] = [G['device']]*ceil(G['N_Bh'])
					b_lbps_result.extend(G['device'])

				b_lbps_result.extend([[]]*(max_K-len(b_lbps_result)))

		msg_warning("access K= %d\t\tN_a= %d\t\tN_Bh= %d"%\
			(len(a_lbps_result),\
				rn_status[device.childs[0].name]['a-subframe-count'],\
				rn_status[device.childs[0].name]['b-subframe-count']),\
			pre=prefix)

		mapping_pattern = m_2hop(device.tdd_config)
		timeline = two_hop_realtimeline(
			mapping_pattern,
			simulation_time,
			b_lbps_result,
			a_lbps_result)

		msg_warning("total awake: %d times" %\
			(sum([1 for i in timeline['backhaul'] if i])+\
			sum([1 for i in timeline['access'] if i])-\
			sum([1 for i in range(len(timeline['access'])) \
				if timeline['backhaul'][i] and timeline['access'][i]]
		)), pre=prefix)

		if check_K:
			return get_sleep_cycle(device, b_lbps_result, a_lbps_result)

		return timeline

	except Exception as e:
		msg_fail(str(e), pre=prefix)

def top_down(b_lbps, device, simulation_time, check_K=False):
	prefix = "TopDown::TD-%s \t" % (b_lbps)
	duplex = 'TDD'
	lbps_scheduling = {
		'aggr': aggr,
		'split': split,
		'merge': merge
	}

	try:
		lbps_result = lbps_scheduling[b_lbps](device, duplex)
		b_lbps_result = [[j.name for j in i] for i in lbps_result]
		lbps_failed = access_aggr(device, lbps_result)
		a_lbps_result = [[j.name for j in i] for i in lbps_result]
		a_lbps_result = [list(set(a_lbps_result[i])-set(b_lbps_result[i]))\
						for i in range(len(a_lbps_result))]

		mapping_pattern = m_2hop(device.tdd_config)
		b_lbps_result = [getDeviceByName(device, i) for i in b_lbps_result]
		a_lbps_result = [getDeviceByName(device, i) for i in a_lbps_result]

		for rn in lbps_failed:
			for TTI in a_lbps_result:
				TTI.append(rn)
				TTI += rn.childs

		timeline = two_hop_realtimeline(
			mapping_pattern,
			simulation_time,
			b_lbps_result,
			a_lbps_result)

		for i in range(len(timeline['backhaul'])):
			timeline['backhaul'][i] = list(set(timeline['backhaul'][i]))
			timeline['access'][i] = list(set(timeline['access'][i]))

		msg_warning("total awake: %d times" %\
			(sum([1 for i in timeline['backhaul'] if i])+\
			sum([1 for i in timeline['access'] if i])-\
			sum([1 for i in range(len(timeline['access'])) \
				if timeline['backhaul'][i] and timeline['access'][i]]
		)), pre=prefix)

		if check_K:
			return get_sleep_cycle(device, b_lbps_result, a_lbps_result)

		return timeline

	except Exception as e:
		msg_fail(str(e), pre=prefix)
		return

def bottom_up(a_lbps, device, simulation_time, check_K=False):
	prefix = "BottomUp::%s \t" % (a_lbps)
	lbps_scheduling = {
		'aggr': min_aggr,
		'split': min_split,
		'merge': merge_merge
	}

	try:
		return lbps_scheduling[a_lbps](device, simulation_time, check_K)

	except Exception as e:
		msg_fail(str(e), pre=prefix)
		return