# -*- coding: utf-8 -*-
#!/usr/bin/python3

import inspect
import random
from network import Bearer, getCQIByType
from config import  traffic


def raiser(err): raise err if type(err) is Exception else raiser(Exception(str(err)))

class Device(Bearer):
	count=0

	def __init__(self, buf={}):
		"""[summary] init

		[description]

		Keyword Arguments:
			buf {dict} -- [description] (default: {{}})
		"""
		self._id = self.__class__.count
		self._buf = buf
		self._link = {'access':[], 'backhaul':[]}
		self._lambd = {'access':0, 'backhaul':0}
		self.__class__.count += 1

	@property
	def id(self):
		return self._id

	@property
	def buf(self):
		return self._buf

	@buf.setter
	def buf(self, buf):
		try:
			if type(buf) is dict:
				buf = {k: v for k, v in buf.items() if k is 'U' or k is 'D'}
				buf = {k: v for k, v in buf.items() if type(v) is int}
				self._buf.update(buf)
			else:
				raise Exception("Buffer should be the type of dict.")
		except Exception as e:
			print(e)

	@property
	def link(self):
		return self._link

	@property
	def lambd(self):
		return self._lambd

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
		try:
			CQI_range = getCQIByType(CQI_type)
			CQI = random.choice(CQI_range) if CQI_range else 0
			me = type(self).__name__ + str(self.id)
			you = type(dest).__name__ + str(dest.id)

			# if self._link[interface]:
			# 	print("%s::connect\t\tdisconnect previous conneciton." % me)

			# print("%s::connect\t\tbuild up a new connection with %s" % (me, you))

			self._link[interface].append(Bearer(self, dest, status, interface, bandwidth, CQI, flow))
			dest._link[interface].append(Bearer(dest, self, status, interface, bandwidth, CQI, flow))

			self._lambd[interface] = sum(tmp.bitrate/tmp.pkt_size for tmp in self._link[interface])
			dest._lambd[interface] = sum(tmp.bitrate/tmp.pkt_size for tmp in dest._link[interface])

			print("%s::connect\t\t%s.lambd = {'access': %g, 'backhaul': %g}\t%s.lambd = {'access': %g, 'backhaul': %g}" \
					% (me, me, self.lambd['access'], self.lambd['backhaul'], you, dest.lambd['access'], dest.lambd['backhaul']))

		except Exception as e:
			print(e);

class UE(Device):
	count = 0

	def __init__(self, buf={}):
		self._id = self.__class__.count
		self._buf = buf
		self._link = {'access':[], 'backhaul':[]}
		self._lambd = {'access':0, 'backhaul':0}
		self.__parent = None
		self.__class__.count += 1
		# print("UE::init::id\t%d" % self.id)

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
		self._id = self.__class__.count
		self._buf = buf
		self._link = {'access':[], 'backhaul':[]}
		self._lambd = {'access':0, 'backhaul':0}
		self.__childs = []
		self.__parent = None
		self.__class__.count += 1
		# print("RN::init::id\t%d" % self.id)

	@property
	def childs(self):
		return self.__childs
	@childs.setter
	def childs(self, childs):
		"""[summary] binding RN and UEs

		[description] only assign the UE as RN's child , no connection

		Decorators:
			childs.setter

		Arguments:
			childs {[UE]} -- [description]

		Raises:
			Exception -- [description]
		"""
		me = type(self).__name__ + str(self.id)
		try:
			childs = list(childs) if childs is not list else childs
			check = list(map(lambda x: Device.isDevice(x, UE), childs))
			if all(check):
				self.__childs = childs
				print("%s::childs.setter\tbinding Done" % me)
			else:
				raise Exception("childs should be all UE instance object")
		except Exception as e:
			print(e)

	def connect(self, status='D', interface='access', bandwidth=0, CQI_type=[], flow='VoIP'):
		"""[summary] connect to own childs

		[description] if there's no childs, this would no do anything

		Keyword Arguments:
			status {str} -- [description] (default: {'D'})
			interface {str} -- [description] (default: {'access'})
			bandwidth {number} -- [description] (default: {0})
			CQI_type {list} -- [description] (default: {[]})
			flow {str} -- [description] (default: {'VoIP'})
		"""
		me = type(self).__name__ + str(self.id)
		if self.childs:
			for i in self.__childs:
				i.connect(self, status, interface, bandwidth, CQI_type, flow)
			print("%s::connect\t\tDone\n" % me)
		else:
			return

# class eNB(Device):
# 	count =0

# 	def __init__(self, buf={}):
# 		self._id = self.__class__.count
# 		self._buf = buf
# 		self._link = {'access':[], 'backhaul':[]}
# 		self._lambd = {'access':0, 'backhaul':0}
# 		self.__childs = []
# 		self.__class__.count += 1
# 		# print("eNB::init::id\t%d" % self.id)

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