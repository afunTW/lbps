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
	def __init__(self, buf={}):
		self._buf = buf
		self._link = {'access':[], 'backhaul':[]}
		self._lambd = {'access':0, 'backhaul':0}
		self._capacity = {'access':None, 'backhaul':None}
		self._virtualCapacity = {'access':None, 'backhaul':None}
		self._sleepCycle = 0
		self._lbpsGroup = None
		self._tdd_config = None

	@property
	def buf(self):
		return self._buf

	@buf.setter
	def buf(self, buf):
		prefix = "%s::buf.setter\t\t" % me
		try:
			if type(buf) is dict:
				buf = {k: v for k, v in buf.items() if k is 'U' or k is 'D'}
				buf = {k: v for k, v in buf.items() if type(v) is int}
				self._buf.update(buf)
			else:
				raise Exception("Buffer should be the type of dict.")
		except Exception as e:
			msg_fail(str(e), pre=prefix)

	@property
	def link(self):
		return self._link

	@property
	def lambd(self):
		return self._lambd

	# Calculate capacity based on interface
	@property
	def capacity(self):
		"""[summary] get the capacity

		[description] using wideband in this simulation
		"""
		me = type(self).__name__ + str(self.id)
		prefix = "%s::capacity\t\t" % me

		try:
			if self._capacity['access'] or self._capacity['backhaul']:
				return self._capacity
			elif self._link:
				self._capacity['access'] = wideband_capacity(self, 'access')
				# self._capacity['backhaul'] = wideband_capacity(self, 'backhaul')
				return self._capacity
			else:
				msg_warning("no capacity", pre=pre)
				return
		except Exception as e:
			msg_fail(str(e), pre=prefix)

	@property
	def virtualCapacity(self):
		me = type(self).__name__ + str(self.id)
		prefix = "%s::virtualCapacity\t" % me

		try:
			if self._virtualCapacity['access'] or self._virtualCapacity['backhaul']:
				return self._virtualCapacity
			elif self._tdd_config and self._link:
				self._virtualCapacity.update(virtual_subframe_capacity(self, 'access', self._tdd_config))
				self._virtualCapacity.update(virtual_subframe_capacity(self, 'backhaul', self._tdd_config))
				return self._virtualCapacity
			elif self._tdd_config:
				msg_fail("there's no connection to estimate CQI calue", pre=prefix)
				return
			else:
				msg_fail("there's no TDD configuration", pre=prefix)
				return
		except Exception as e:
			msg_fail(str(e), pre=prefix)

	@property
	def sleepCycle(self):
	    return self._sleepCycle

	@sleepCycle.setter
	def sleepCycle(self, K):
		self._sleepCycle = K

	@property
	def lbpsGroup(self):
	    return self._lbpsGroup

	@lbpsGroup.setter
	def lbpsGroup(self, group):
		self._lbpsGroup = group if type(group) is int else None

	@property
	def tdd_config(self):
	    return self._tdd_config

	@tdd_config.setter
	def tdd_config(self, config):
		me = type(self).__name__ + str(self.id)
		prefix = "%s::tdd_config.setter\t" % me

		if config in ONE_HOP_TDD_CONFIG.values() or config in TWO_HOP_TDD_CONFIG.values():
			self._tdd_config = config
		else:
			msg_fail("wrong tdd config setting", pre=prefix)

	def isDevice(testDevice, targetClass):
		return True if isinstance(testDevice, targetClass) else False

	def connect(self, dest, status='D', interface='access', bandwidth=0, CQI_type=[], flow='VoIP'):
		"""[summary] build up a connection one by one

		[description]
			1. build up a bearer between two device
			2. append to link list
			3. calculate lambda

		Arguments:
			dest {[type]} -- [description]

		Keyword Arguments:
			status {str} -- [description] (default: {'D'})
			interface {str} -- [description] (default: {'access'})
			bandwidth {number} -- [description] (default: {0})
			CQI_type {list} -- [description] (default: {[]})
			flow {str} -- [description] (default: {'VoIP'})
		"""
		me = type(self).__name__ + str(self.id)
		you = type(dest).__name__ + str(dest.id)
		prefix = "%s::connect\t\t" % me

		try:
			CQI_range = getCQIByType(CQI_type)
			CQI = random.choice(CQI_range) if CQI_range else 0

			# if self._link[interface]:
			# 	msg_warning("disconnect previous conneciton", pre=pre)

			self._link[interface].append(Bearer(self, dest, status, interface, bandwidth, CQI, flow))
			dest._link[interface].append(Bearer(dest, self, status, interface, bandwidth, CQI, flow))

			self._lambd[interface] = sum(tmp.bitrate/tmp.pkt_size for tmp in self._link[interface])
			dest._lambd[interface] = sum(tmp.bitrate/tmp.pkt_size for tmp in dest._link[interface])

			# msg_execute("%s.lambd = {'access': %g, 'backhaul': %g}\t%s.lambd = {'access': %g, 'backhaul': %g}\t(pkt_size/ms)" \
			# 		% (me, self.lambd['access'], self.lambd['backhaul'], you, dest.lambd['access'], dest.lambd['backhaul']), pre=pre)

		except Exception as e:
			msg_fail(str(e), pre=prefix);

class UE(Device):
	count = 0

	def __init__(self, buf={}):
		Device.__init__(self, buf)
		self._id = self.__class__.count
		self.__parent = None
		self.__class__.count += 1

	@property
	def id(self):
		return self._id

	@property
	def parent(self):
		return self.__parent

	@parent.setter
	def parent(self, pD):
		try:
			self.__parent = pD if UE.isDevice(pD, RN) else raiser(Exception("parent should be type of RN instance"))
		except Exception as e:
			print(e)

class RN(Device):
	count = 0

	def __init__(self, buf={}):
		Device.__init__(self, buf)
		self._id = self.__class__.count
		self.__childs = []
		self.__parent = None
		self.__class__.count += 1

	@property
	def id(self):
		return self._id

	@property
	def childs(self):
		return self.__childs

	@childs.setter
	def childs(self, childs):
		me = type(self).__name__ + str(self.id)
		pre = "%s::childs.setter\t" % me

		try:
			childs = list(childs) if childs is not list else childs
			check = list(map(lambda x: Device.isDevice(x, UE), childs))
			if all(check):
				self.__childs = childs
				msg_success("binding Done", pre=pre)

		except Exception as e:
			print(e)

	def connect(self, status='D', interface='access', bandwidth=0, CQI_type=[], flow='VoIP'):
		me = type(self).__name__ + str(self.id)
		pre = "%s::connect\t\t" % me
		if self.childs:
			for i in self.__childs:
				i.connect(self, status, interface, bandwidth, CQI_type, flow)
			msg_success("Done", pre=pre)
		else:
			return

# class eNB(Device):
# 	count =0

# 	def __init__(self, buf={}):
# 		self._id = self.__class__.count
# 		self.__childs = []
# 		self.__class__.count += 1

# 	@property
# 	def childs(self):
# 		return self.__childs

# 	@childs.setter
# 	def childs(self, childs):
# 		me = type(self).__name__ + str(self.id)
# 		try:
# 			childs = list(childs) if childs is not list else childs
# 			check = list(map(lambda x: Device.isDevice(x, RN), childs))
# 			if all(check):
# 				self.__childs = childs
# 				print("%s::childs.setter\tbinding Done" % me)
# 			else:
# 				raise Exception("childs should be all RN instance object")
# 		except Exception as e:
# 			print(e)

# 	def connect(self, status='D', interface='backhaul', bandwidth=0, CQI_type=[], flow='VoIP'):
# 		me = type(self).__name__ + str(self.id)
# 		if self.childs:
# 			for i in self.__childs:
# 				i.connect(self, status, interface, bandwidth, CQI_type, flow)
# 			print("%s::connect\t\tDone\n" % me)
# 		else:
# 			return
# if __name__ == '__main__':