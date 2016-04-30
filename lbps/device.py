# -*- coding: utf-8 -*-
#!/usr/bin/python3

import inspect
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
		self._sleepCycle = 0
		self._wakeUpTimes = 0
		self._lbpsGroup = None
		self._tdd_config = None

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

	# Calculate capacity based on interface
	@property
	def capacity(self):
		"""[summary] get the capacity

		[description] using wideband in this simulation
		"""
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
	def sleepCycle(self):
		# msg_execute(str(self._sleepCycle), pre="%s::sleepCycle \t" % self._name)
		return self._sleepCycle

	@sleepCycle.setter
	def sleepCycle(self, K):
		self._sleepCycle = K

	@property
	def wakeUpTimes(self):
		msg_execute(str(self._wakeUpTimes), pre="%s::wakeUpTimes\t" % self._name)
		return self._wakeUpTimes

	@wakeUpTimes.setter
	def wakeUpTimes(self, n):
		self._wakeUpTimes = n if type(n) is int else 0

	@property
	def lbpsGroup(self):
		# msg_execute("Group number: %s" % str(self._lbpsGroup), pre="%s::lbpsGroup\t\t" % self._name)
		return self._lbpsGroup

	@lbpsGroup.setter
	def lbpsGroup(self, group):
		self._lbpsGroup = group if type(group) is int else None

	@property
	def tdd_config(self):
		# msg_execute(str(self._tdd_config), pre="%s::tdd_config \t" % self._name)
		return self._tdd_config

	@tdd_config.setter
	def tdd_config(self, config):
		pre = "%s::tdd_config.setter\t" % self._name

		try:

			if config in ONE_HOP_TDD_CONFIG.values() or config in TWO_HOP_TDD_CONFIG.values():
				self._tdd_config = config

			self.virtualCapacity

		except Exception as e:
			msg_fail(str(e), pre=pre)

	def connect(self, dest, status='D', interface='access', bandwidth=0, CQI_type=[], flow='VoIP'):
		"""[summary] build up a connection one by one

		[description]
			1. build up a bearer between two device
			2. append to link list
			3. calculate lambda
		"""

		me = self._name
		you = dest._name
		pre = "%s::connect\t\t" % me

		try:

			CQI_range = getCQIByType(CQI_type)
			CQI = random.choice(CQI_range) if CQI_range else 0

			self._link[interface].append(Bearer(self, dest, status, interface, bandwidth, CQI, flow))
			dest._link[interface].append(Bearer(dest, self, status, interface, bandwidth, CQI, flow))

			self._lambd[interface] = sum(tmp.bitrate/tmp.pkt_size for tmp in self._link[interface])
			dest._lambd[interface] = sum(tmp.bitrate/tmp.pkt_size for tmp in dest._link[interface])

			# msg_execute("%s.lambd = {'access': %g, 'backhaul': %g}\t%s.lambd = {'access': %g, 'backhaul': %g}\t(pkt_size/ms)" \
			# 		% (me, self.lambd['access'], self.lambd['backhaul'], you, dest.lambd['access'], dest.lambd['backhaul']), pre=pre)

		except Exception as e:
			msg_fail(str(e), pre=pre);

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
				msg_success("Done", pre=pre)

		except Exception as e:
			msg_fail(e, pre=pre)

	@property
	def parent(self):
		return self.__parent

	@parent.setter
	def parent(self, parent):
		self.__parent = parent if isinstance(parent, eNB) else None

	def connect(self, status='D', interface='access', bandwidth=0, CQI_type=[], flow='VoIP'):
		pre = "%s::childs.connect\t" % self.__name

		try:

			if interface is 'access' and self.__childs:
				for i in self.__childs:
					super().connect(i, status, interface, bandwidth, CQI_type, flow)

			elif interface is 'backhaul' and self.__parent:
				super().connect(self.__parent, status, interface, bandwidth, CQI_type, flow)

		except Exception as e:
			msg_fail(str(e), pre=pre)

class eNB(Device):
	count = 0

	def __init__(self, buf={}):
		self.__id = self.__class__.count
		self.__name = self.__class__.__name__ + str(self.__id)
		self.__childs = []
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
			check = list(map(lambda x: Device.isDevice(x, RN), childs))

			if all(check):
				self.__childs = childs
				msg_success("binding Done", pre=pre)

		except Exception as e:
			msg_fail(str(e), pre=pre)

	def connect(self, status='D', interface='backhaul', bandwidth=0, CQI_type=[], flow='VoIP'):
		pre = "%s::childs.connect\t" % self.__name

		try:

			if interface is 'backhaul' and self.__childs:
				for i in self.__childs:
					super().connect(i, status, interface, bandwidth, CQI_type, flow)

		except Exception as e:
			msg_fail(str(e), pre=pre)