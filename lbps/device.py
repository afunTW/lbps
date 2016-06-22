# -*- coding: utf-8 -*-
#!/usr/bin/python3

import random
import math
from network import Bearer, getCQIByType
from config import *
from tdd import *
from viewer import *

def raiser(err): raise err if type(err) is Exception else raiser(Exception(str(err)))

class Device(Bearer):

	def __init__(self, name=None):
		self._name = name
		self._buf = {'D': [], 'U': []}
		self._link = {'access':[], 'backhaul':[]}
		self._tdd_config = None
		self._CQI = 0
		self._sleep_mode = False

	@property
	def buf(self):
		# msg_execute(str(self._buf), pre="%s::buf\t\t" % self._name)
		return self._buf

	@buf.setter
	def buf(self, buf):
		pre = "%s::buf.setter\t\t" % self._name
		try:
			if type(buf) is dict:
				buf = {k: v for k, v in buf.items() if k is 'U' or k is 'D'}
				buf = {k: v for k, v in buf.items() if type(v) is int}
				self._buf.update(buf)
		except Exception as e:
			msg_fail(str(e), pre=pre)

	@property
	def name(self):
		return self._name

	@property
	def link(self):
		return self._link

	@property
	def lambd(self):
		return {
			'backhaul': round(sum([traffic[b.flow]['lambda'] for b in self.link['backhaul']]),2),
			'access': round(sum([traffic[a.flow]['lambda'] for a in self.link['access']]),2)
		}

	@property
	def capacity(self):
		pre = "%s::capacity\t\t" % self._name

		if self._CQI:
			return int(N_TTI_RE*T_CQI[self._CQI]['eff'])

		msg_fail("failed", pre=pre)
		return

	@property
	def virtualCapacity(self):
		pre = "%s::virtualCapacity\t" % self._name

		if self.tdd_config:
			return int(self.tdd_config.count('D')*self.capacity/10)

		msg_fail("failed", pre=pre)
		return

	@property
	def tdd_config(self):
		return self._tdd_config

	@tdd_config.setter
	def tdd_config(self, config):
		pre = "%s::tdd_config.setter\t" % self._name

		try:
			if config in ONE_HOP_TDD_CONFIG.values():
				self._tdd_config = config

		except Exception as e:
			msg_fail(str(e), pre=pre)

	@property
	def CQI(self):
		return self._CQI

	@CQI.setter
	def CQI(self, CQI):
		pre="%s::CQI.setter\t\t" % self._name

		try:
			if type(CQI) is list:
				CQI_range = getCQIByType(CQI)
				self._CQI = random.choice(CQI_range) if CQI_range else 0
			elif type(CQI) is int and 0<CQI<=15:
				self._CQI = CQI

		except Exception as e:
			msg_fail(str(e), pre=pre)

	@property
	def sleep_mode(self):
		return self._sleep_mode

	@sleep_mode.setter
	def sleep_mode(self, sw):
		if type(sw) is bool:
			self._sleep_mode = sw

	def connect(self, dest, status='D', interface='access', bandwidth=0, flow='VoIP'):

		me = self._name
		you = dest._name
		pre = "%s::connect\t\t" % me

		try:
			bearer = Bearer(self, dest, status, interface, bandwidth, flow)
			self._link[interface].append(bearer)
			dest.link[interface].append(bearer)

		except Exception as e:
			msg_fail("failed: " + str(e), pre=pre);

class UE(Device):
	count = 0

	def __init__(self):
		self.__id = self.__class__.count
		self.__name = self.__class__.__name__ + str(self.__id)
		self.__parent = None
		self.__class__.count += 1
		super().__init__(self.__name)

	@property
	def parent(self):
		return self.__parent

	@parent.setter
	def parent(self, pD):
		self.__parent = pD if isinstance(pD, RN) else None

	@Device.lambd.getter
	def lambd(self):
		return {
			'access': round(sum([traffic[a.flow]['lambda'] for a in self.link['access']]), 2)
		}

class RN(Device):
	count = 0

	def __init__(self):
		self.__id = self.__class__.count
		self.__name = self.__class__.__name__ + str(self.__id)
		self.__childs = []
		self.__parent = None
		self.__queue = {'backhaul':[], 'access':{}}
		self.__class__.count += 1
		super().__init__(self.__name)

	@property
	def childs(self):
		return self.__childs

	@childs.setter
	def childs(self, childs):
		pre = "%s::childs.setter\t" % self.__name

		try:

			childs = list(childs) if type(childs) is not list else childs
			check = list(map(lambda x: isinstance(x, UE), childs))

			if all(check):
				self.__childs = childs
				# msg_success("success", pre=pre)

		except Exception as e:
			msg_fail(e, pre=pre)

	@property
	def parent(self):
		return self.__parent

	@property
	def queue(self):
		return self.__queue

	@parent.setter
	def parent(self, parent):
		self.__parent = parent if isinstance(parent, eNB) else None

	@Device.lambd.getter
	def lambd(self):
		lambd = round(sum([ue.lambd['access'] for ue in self.childs]), 2)
		return {
			'backhaul': lambd,
			'access': lambd
		}

	@Device.capacity.getter
	def capacity(self):
		pre = "%s::capacity\t" % self.name

		try:
			return {
				'backhaul': super().capacity,
				'access': wideband_capacity(self)
			}

		except Exception as e:
			msg_fail(str(e), pre=pre)

	@Device.virtualCapacity.getter
	def virtualCapacity(self):
		pre = "%s::virtualCapacity\t" % self._name

		if self.tdd_config and self.capacity['access']:
			n_subframe = self.tdd_config.count('D')-self.parent.tdd_config.count('D')

			if self.__parent.idle_capacity:
				n_subframe += self.__parent.idle_capacity

			return int(n_subframe*self.capacity['access']/10)

		msg_fail("failed", pre=pre)
		return

	@Device.tdd_config.setter
	def tdd_config(self, config):
		pre = "%s::tdd_config.setter\t" % self._name

		try:

			if config in ONE_HOP_TDD_CONFIG.values():
				self._tdd_config = config
				for i in self.__childs:
					i.tdd_config = config

		except Exception as e:
			msg_fail(str(e), pre=pre)

	# override Device.connect
	def connect(self, dest, status='D', interface='access', bandwidth=0, flow='VoIP'):
		try:
			pre = "%s::connect\t\t" % self.name
			super().connect(dest, status, interface, bandwidth, flow)
			interface == 'access' and self.__queue[interface].update({dest.name:[]})

		except Exception as e:
			msg_fail(str(e), pre=pre)

class eNB(Device):
	count = 0

	def __init__(self):
		self.__id = self.__class__.count
		self.__name = self.__class__.__name__ + str(self.__id)
		self.__childs = []
		self.__queue = {'backhaul':{}, 'access':[]}
		self.__class__.count += 1
		super().__init__(self.__name)

	@property
	def childs(self):
		return self.__childs

	@childs.setter
	def childs(self, childs):
		pre = "%s::childs.setter\t" % self.__name

		try:

			childs = list(childs) if type(childs) is not list else childs
			check = list(map(lambda x: isinstance(x, RN), childs))

			if all(check):
				self.__childs = childs
				# msg_success("success", pre=pre)

		except Exception as e:
			msg_fail(str(e), pre=pre)

	@property
	def queue(self):
		return self.__queue

	@property
	def idle_capacity(self):
		return self._idle_capacity

	@Device.lambd.getter
	def lambd(self):
		lambd = round(sum([rn.lambd['backhaul'] for rn in self.childs]), 2)
		return {
			'backhaul': lambd
		}

	@Device.capacity.getter
	def capacity(self):
		pre = "%s::capacity\t" % self.name
		try:
			return wideband_capacity(self)
		except Exception as e:
			msg_fail(str(e), pre=pre)

	@Device.tdd_config.setter
	def tdd_config(self, config):
		pre = "%s::tdd_config.setter\t" % self.name

		try:

			if config in ONE_HOP_TDD_CONFIG.values():
				self._tdd_config = config

			elif config in TWO_HOP_TDD_CONFIG.values():
				self._tdd_config = config['backhaul']
				for i in self.__childs:
					i.tdd_config = config['access']
					for j in i.childs:
						j.tdd_config = config['access']

		except Exception as e:
			msg_fail(str(e), pre=pre)

	@Device.CQI.getter
	def CQI(self):
		pre = "%s::CQI\t\t" % self.name

		if self.childs:
			return int(sum([rn.CQI for rn in self.childs])/len(self.childs))

		msg_fail("failed", pre=pre)

	# override Device.connect
	def connect(self, dest, status='D', interface='access', bandwidth=0, flow='VoIP'):
		try:
			pre = "%s::connect\t\t" % self.name
			super().connect(dest, status, interface, bandwidth, flow)
			interface == 'backhaul' and self.__queue[interface].update({dest.name:[]})

		except Exception as e:
			msg_fail(str(e), pre=pre)

	def clearQueue(self):
		try:
			pre = "%s::clearQueue\t\t" % self.name
			for rn in self.childs:
				self.__queue['backhaul'][rn.name] = []
				rn.queue['backhaul'] = []
				for ue in rn.childs:
					rn.queue['access'][ue.name] = []
		except Exception as e:
			msg_fail(str(e), pre=pre)

	def choose_tdd_config(self, timeline, fixed=None):

		# decide 2-hop TDD configuration (DL)
		candidate = TWO_HOP_TDD_CONFIG.copy()
		max_b_subframe = max([candidate[i]['backhaul'].count('D') for i in candidate])
		max_a_subframe = max([candidate[i]['access'].count('D') for i in candidate])
		radio_frame_pkt = [pkt for TTI in timeline for pkt in timeline[TTI] if TTI <= 10]
		total_pktSize = sum([traffic[pkt['flow']]['pkt_size'] for pkt in radio_frame_pkt])


		if fixed and type(fixed) is int and 0<=fixed<19:
			n_b_subframe = TWO_HOP_TDD_CONFIG[fixed]['backhaul'].count('D')
			required_b_subframe = total_pktSize/self.capacity
			required_b_subframe = required_b_subframe\
			if required_b_subframe<=n_b_subframe else n_b_subframe
			self._idle_capacity = round(n_b_subframe-required_b_subframe, 2)
			self.tdd_config = TWO_HOP_TDD_CONFIG[fixed]
		else:
			# backhaul and access filter for TDD configuration decision
			n_b_subframe = math.ceil(total_pktSize/self.capacity)
			n_b_subframe = n_b_subframe if n_b_subframe <= max_b_subframe else max_b_subframe
			n_a_subframe = max([math.ceil(total_pktSize/len(self.childs)/i.capacity['access']) for i in self.childs])
			n_a_subframe = n_a_subframe if n_a_subframe <= max_a_subframe else max_a_subframe
			self._idle_capacity = round(n_b_subframe-(total_pktSize/self.capacity), 2)

			candidate = {i: candidate[i] for i in candidate if candidate[i]['backhaul'].count('D') >= n_b_subframe}
			candidate = {i: candidate[i] for i in candidate if candidate[i]['access'].count('D') >= n_a_subframe} \
						if len(candidate) > 1 else candidate

			b_sort = sorted(candidate, key=lambda x: candidate[x]['backhaul'].count('D'))
			b_sort = candidate[b_sort[0]]['backhaul'].count('D')
			candidate = {i: candidate[i] for i in candidate if candidate[i]['backhaul'].count('D') == b_sort}
			a_sort = sorted(candidate, key=lambda x: candidate[x]['access'].count('D'))
			a_sort = candidate[a_sort[0]]['access'].count('D')
			candidate = {i: candidate[i] for i in candidate if candidate[i]['access'].count('D') == a_sort}

			candidate_key = random.choice(list(candidate.keys()))
			self.tdd_config = candidate[candidate_key] if candidate else None

		if not self.tdd_config:
			msg_fail("no suitable TDD configuration")

	def simulate_timeline(self, simulation_time):
		try:
			# calc pre-inter-arrival-time of packets (encapsulate)
			users = [ue for rn in self.childs for ue in rn.childs]
			timeline = { i:[] for i in range(simulation_time+1)}

			# assign pre-calc pkt arrival to timeline
			for i in range(len(users)):

				for bearer in users[i].link['access']:
					arrTimeByBearer = [0]

					# random process of getting inter-arrival-time by bearer
					while arrTimeByBearer[-1]<=simulation_time and users[i].lambd['access']:
						arrTimeByBearer.append(arrTimeByBearer[-1]+random.expovariate(users[i].lambd['access']))
					arrTimeByBearer[-1] > simulation_time and arrTimeByBearer.pop()
					arrTimeByBearer.pop(0)

					# assign pkt to real timeline
					for arrTime in range(len(arrTimeByBearer)):
						pkt = {
							'device': users[i],
							'flow': bearer.flow,
							'size': traffic[bearer.flow]['pkt_size'],
							'delay_budget': traffic[bearer.flow]['delay_budget'],
							'bitrate': traffic[bearer.flow]['bitrate'],
							'arrival_time': arrTimeByBearer[arrTime]
						}
						timeline[math.ceil(pkt['arrival_time'])].append(pkt)

			for i in range(len(timeline)):
				timeline[i] = sorted(timeline[i], key=lambda x: x['arrival_time'])

			return timeline

		except Exception as e:
			msg_fail(str(e), end='\t')