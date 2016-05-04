# -*- coding: utf-8 -*-
#!/usr/bin/python3

import random
from network import Bearer, getCQIByType
from config import  traffic, wideband_capacity
from tdd import *
from viewer import *

def raiser(err): raise err if type(err) is Exception else raiser(Exception(str(err)))

class Device(Bearer):

	def __init__(self, buf={}, name=None):
		self._buf = buf
		self._name = name
		self._link = {'access':[], 'backhaul':[]}
		self._lambd = {'access':0, 'backhaul':0}
		self._capacity = {'access':None, 'backhaul':None}
		self._virtualCapacity = {'access':None, 'backhaul':None}
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
		# msg_execute(str(self._lambd), pre="%s::lambd\t\t" % self._name)
		return self._lambd

	@property
	def capacity(self):
		pre = "%s::capacity\t\t" % self._name

		try:

			if self._capacity['access'] and self._capacity['backhaul']:
				# msg_execute(str(self._capacity), pre=pre)
				return self._capacity

			elif self._link:
				self._capacity['access'] = wideband_capacity(self, 'access')
				self._capacity['backhaul'] = wideband_capacity(self, 'backhaul')
				# msg_execute(str(self._capacity), pre=pre)
				return self._capacity

			else:
				msg_warning("no capacity", pre=pre)
				return

		except Exception as e:
			msg_fail(str(e), pre=pre)

	@property
	def virtualCapacity(self):
		pre = "%s::virtualCapacity\t" % self._name

		try:

			if self._virtualCapacity['access'] or self._virtualCapacity['backhaul']:
				# msg_execute(str(self._virtualCapacity), pre=pre)
				return self._virtualCapacity

			elif self._tdd_config and self._link:
				self._virtualCapacity.update(virtual_subframe_capacity(self, 'access', self._tdd_config))
				self._virtualCapacity.update(virtual_subframe_capacity(self, 'backhaul', self._tdd_config))
				# msg_execute(str(self._virtualCapacity), pre=pre)
				return self._virtualCapacity

			elif self._tdd_config:
				msg_fail("there's no connection to estimate CQI calue", pre=pre)
				return

			else:
				msg_fail("there's no TDD configuration", pre=pre)
				return

		except Exception as e:
			msg_fail(str(e), pre=pre)

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
	def CQI(self, typeCQI):
		try:
			pre="%s::CQI.setter\t\t" % self._name
			CQI_range = getCQIByType(typeCQI)
			self._CQI = random.choice(CQI_range) if CQI_range else 0

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
			self._lambd[interface] = sum(traffic[l.flow]['bitrate']/traffic[l.flow]['pkt_size'] for l in self._link[interface])
			dest.link[interface].append(bearer)
			dest.lambd[interface] = sum(traffic[l.flow]['bitrate']/traffic[l.flow]['pkt_size'] for l in dest.link[interface])
			# msg_success("connect to %s success" % you, pre=pre)

		except Exception as e:
			msg_fail("failed: " + str(e), pre=pre);

class UE(Device):
	count = 0

	def __init__(self, buf={}):
		self.__id = self.__class__.count
		self.__name = self.__class__.__name__ + str(self.__id)
		self.__parent = None
		self.__class__.count += 1
		super().__init__(buf, self.__name)

	@property
	def parent(self):
		return self.__parent

	@parent.setter
	def parent(self, pD):
		self.__parent = pD if isinstance(pD, RN) else None

class RN(Device):
	count = 0

	def __init__(self, buf={}):
		self.__id = self.__class__.count
		self.__name = self.__class__.__name__ + str(self.__id)
		self.__childs = []
		self.__parent = None
		self.__queue = {'backhaul':[], 'access':{}}
		self.__class__.count += 1
		super().__init__(buf, self.__name)

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

	@Device.tdd_config.setter
	def tdd_config(self, config):
		pre = "%s::tdd_config.setter\t" % self._name

		try:

			if config in ONE_HOP_TDD_CONFIG.values() and self.__childs:
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

	def __init__(self, buf={}):
		self.__id = self.__class__.count
		self.__name = self.__class__.__name__ + str(self.__id)
		self.__childs = []
		self.__queue = {'internet': [], 'backhaul':{}}
		self.__class__.count += 1
		super().__init__(buf, self.__name)

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

	@Device.tdd_config.setter
	def tdd_config(self, config):
		pre = "%s::tdd_config.setter\t" % self._name

		try:

			if config in ONE_HOP_TDD_CONFIG.values():
				self._tdd_config = config

			elif config in TWO_HOP_TDD_CONFIG.values():
				self._tdd_config = config['backhaul']
				for i in self.__childs:
					i._tdd_config = config['access']

		except Exception as e:
			msg_fail(str(e), pre=pre)

	# override Device.connect
	def connect(self, dest, status='D', interface='access', bandwidth=0, flow='VoIP'):
		try:
			pre = "%s::connect\t\t" % self.name
			super().connect(dest, status, interface, bandwidth, flow)
			interface == 'backhaul' and self.__queue[interface].update({dest.name:[]})

		except Exception as e:
			msg_fail(str(e), pre=pre)