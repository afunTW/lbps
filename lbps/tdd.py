import copy
from viewer import msg_fail, msg_warning
from config import *
from math import ceil
from pprint import pprint

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
				if rs['RSC'] >= vs['VSC']:
					rs['RSC'] -= vs['VSC']
					vs['VSC'] = 0
					vs['r_TTI'].append(rs['r_TTI'])
					break
				else:
					vs['VSC'] -= rs['RSC']
					rs['RSC'] = 0
					vs['r_TTI'].append(rs['r_TTI'])
			config = [i for i in config if i['RSC']]

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

def two_hop_mapping(TDD_config, a_RSC, a_VSC):

	pre = "mapping::2hop\t\t"

	try:
		if not is_backhaul_config(TDD_config):
			raise Exception("only accept backhaul TDD configuration as input")

		backhaul_config = copy.deepcopy(TDD_config)
		access_config = get_access_by_backhaul_config(backhaul_config)

		# backhaul mapping (M2)
		v_timeline = {
			'backhaul': continuous_mapping(backhaul_config),
			'access': [{'r_TTI':[], 'VSC':a_VSC, 'identity':[]} for i in range(10)]}

		# access mapping: access only(M3) > mixed(M2) > backhaul maybe(M2)
		access_only = get_access_by_backhaul_config(backhaul_config, no_backhaul=True)
		access_only = [{'r_TTI': i, 'RSC':a_RSC} for i in range(10) if access_only[i] is 'D']
		backhaul_maybe = [{'r_TTI': i, 'RSC':a_RSC} for i in range(10) if backhaul_config[i] is 'D']

		# access only
		M3_index = 0
		mixed_subframe = False
		for i in v_timeline['access']:

			# one to one
			if access_only[M3_index]['RSC'] >= i['VSC']:
				access_only[M3_index]['RSC'] -= i['VSC']
				i['VSC'] = 0
				i['r_TTI'].append(access_only[M3_index]['r_TTI'])
				i['identity'] = 'access'
				M3_index = (M3_index+1)%len(access_only)
				continue

			# check mixed suvframe probability
			if sum([ao['RSC'] for ao in access_only]) < a_VSC:
				mixed_subframe = i
				break

			# one to many
			for j in access_only:
				if i['VSC'] == 0:
					break
				if j['RSC'] == 0:
					continue

				i['r_TTI'].append(j['r_TTI'])
				i['identity'] = 'access'

				if j['RSC'] >= i['VSC']:
					j['RSC'] -= i['VSC']
					i['VSC'] = 0
				else:
					i['VSC'] -= j['RSC']
					j['RSC'] = 0

		# mixed subframe
		if mixed_subframe:
			mixed_subframe['identity'] = 'mixed'

			for ao in access_only:
				if ao['RSC'] == 0:
					continue

				mixed_subframe['r_TTI'].append(ao['r_TTI'])
				mixed_subframe['VSC'] -= ao['RSC']
				ao['RSC'] = 0

			if mixed_subframe['VSC'] > backhaul_maybe[0]['RSC']:
				raise Exception("algorithm design error")

			backhaul_maybe[0]['RSC'] -= mixed_subframe['VSC']
			mixed_subframe['r_TTI'].append(backhaul_maybe[0]['r_TTI'])
			mixed_subframe['VSC'] = 0

		# backhaul maybe (M2)
		for i in v_timeline['access']:
			if i['VSC'] == 0:
				continue

			for j in backhaul_maybe:
				if i['VSC'] == 0:
					break
				if j['RSC'] == 0:
					continue

				i['r_TTI'].append(j['r_TTI'])
				i['identity'] = 'backhaul'

				if j['RSC'] >= i['VSC']:
					j['RSC'] -= i['VSC']
					i['VSC'] = 0
				else:
					i['VSC'] -= j['RSC']
					j['RSC'] = 0

		v_timeline ={
			'backhaul':v_timeline['backhaul'],
			'access': [{'r_TTI':i['r_TTI'], 'identity':i['identity']} for i in v_timeline['access']]}

		return v_timeline

	except Exception as e:
		msg_fail(str(e), pre=pre)
