# -*- coding: utf-8 -*-
#!/usr/bin/python3

import inspect
import random
from network import Bearer, getCQIByType
from config import  traffic


def raiser(err): raise err if type(err) is Exception else raiser(Exception(str(err)))

class Device(Bearer):
	count=0;

	def __init__(self, buf={}):
		"""[summary] init

		[description]

		Keyword Arguments:
			buf {dict} -- [description] (default: {{}})
		"""
		self._id = self.__class__.count;
		self._buf = buf
		self._link = None;
		self._lambd = None;
		self.__class__.count += 1;

	@property
	def id(self):
		return self._id

	@property
	def buf(self):
		return self._buf

	@buf.setter
	def buf(self, buf):
		"""[summary] check type and assign buffer approprite

		[description]
		maintain the buffer always have only two items with key 'U' and 'D'
		and the value are always in type int

		Decorators:
			buf.setter

		Arguments:
			buf {[dict]} -- [description]

		Raises:
			Exception -- [description]
		"""
		try:
			if type(buf) is dict:
				buf = {k: v for k, v in buf.items() if k is 'U' or k is 'D'}
				buf = {k: v for k, v in buf.items() if type(v) is int}
				self._buf.update(buf)
			else:
				raise Exception("Buffer should be the type of dict.")
		except Exception as e:
			print(e);

	@property
	def link(self):
		return self._link

	@property
	def lambd(self):
		return self._lambd

	def isDevice(testDevice, targetClass):
		return True if isinstance(testDevice, targetClass) else False

	def connect(self, dest, status='D', interface='access', bandwidth=0, CQI=0, flow='VoIP'):
		"""[summary] build up connection

		[description]
			build up a bearer and update the related info

		Arguments:
			dest {object} -- [destination device]

		Keyword Arguments:
			status {str} -- [identify the flow direction] (default: {'D'})
			interface {str} -- [identify the link type] (default: {'access'})
			bandwidth {number} -- [description] (default: {0})
			CQI {number} -- [random number from 0 to 15] (default: {0})
			flow {str} -- [reference to config.py] (default: {'VoIP'})
		"""
		try:
			if self._link:
				print("Disconnect previous conneciton.");
			print("Build up a new connection with " + str(dest))
			self._link = Bearer(self, dest, status, interface, bandwidth, CQI, flow);
			self._lambd = self._link.bitrate / self._link.pkt_size;
		except Exception as e:
			print(e);


class UE(Device):
	count = 0

	def __init__(self, buf={}):
		"""[summary] init

		[description]

		Keyword Arguments:
			buf {dict} -- [description] (default: {{}})
		"""
		self._id = self.__class__.count
		self._buf = buf
		self._link = None;
		self._lambd = None;
		self.__parent = None;
		self.__class__.count += 1
		print("UE::init::id\t%d" % self.id)

	@property
	def parent(self):
		return self.__parent;

	@parent.setter
	def parent(self, pD):
		try:
			self.__parent = pD if UE.isDevice(pD, RN) else raiser(Exception("parent should be type of RN instance"));
		except Exception as e:
			print(e);

	def connect(self, CQI_type, status='D', interface='access', bandwidth=0, CQI=0, flow='VoIP'):
		if  not self.__parent:
			print("UE::connect\tno parent device to connect with");
			return;
		try:
			if self._link:
				print("UE::connect\tdisconnect previous conneciton.");
			print("UE::connect\tbuild up a new connection with " + str(self.__parent))
			self._link = Bearer(self, self.__parent, status, interface, bandwidth, CQI, flow);
			self._lambd = self._link.bitrate / self._link.pkt_size;
		except Exception as e:
			print(e);


class RN(Device):
	count = 0

	def __init__(self, buf={}):
		"""[summary] init

		[description]

		Keyword Arguments:
			buf {dict} -- [description] (default: {{}})
		"""
		self._id = self.__class__.count
		self._buf = buf
		self._link = {};
		self._lambd = None
		self.__RUE = [];
		self.__class__.count += 1
		print("RN::init::id\t%d" % self.id)

	@property
	def RUE(self):
		return self.__RUE
	@RUE.setter
	def RUE(self, RUE):
		"""[summary]

		[description]
			ensure the served UE list and aggregate the lambda as own value
			and the link property is the type of dict, collect all served UEs bearer
			# FIXME: append() would pass any value

		Decorators:
			RUE.setter

		Arguments:
			RUE {[list]} -- [description]

		Raises:
			Exception -- [description]
		"""
		try:
			RUE = list(RUE) if RUE is not list else RUE
			check = list(map(lambda x: RN.isDevice(x, UE), RUE))
			if all(check):
				self.__RUE = RUE
				print("RN::RUE.setter\tsetter Done")

				list(map(self._link['access'].append, self.__RUE.link));
				print("RN::RUE.setter\tappend the served bearer to link['access']");

				# FIXME: random.choice(CQI_range)

				self._lambd = sum(self.__RUE.link.bitrate) / sum(self.__RUE.link.pkt_size);
				print("RN::RUE.setter::lambd\tRN.lambd = " + str(self._lambd))
			else:
				raise Exception("RUE should be all UE instance object")
		except Exception as e:
			print(e)


class eNB(Device):
	count =0;

	def __init__(self, buf={}):
		"""
		@property
		[protected]	id: eNB id
		[protected]	buf
		[protected]	status
		[protected]	link
		[protected]	lambd
		[private]	relays: a list of served RN
		"""
		self._id = self.__class__.count;
		self._buf = buf
		# self._status = status;
		# self._link = Bearer(link, bandwidth, CQI);
		# self._lambd = 0;
		# self.__relays = relay;
		self.__class__.count += 1;

	@property
	def relays(self):
		return self.__relays

	@relays.setter
	def relays(self, relays):
		"""
		similar to RN.RUE setter
		"""
		try:
			relays = list(relays) if relays is not list else relays
			check = list(map(lambda x: eNB.isDevice(x, RN), relays))
			if all(check):
				self.__relays = relays
				# FIXME: lambd = bitrate/pkt_size
				# self._lambd = sum(rn.lambd for rn in self.__relays);
			else:
				raise Exception("RUE should be all UE instance object")
		except Exception as e:
			print(e)

if __name__ == '__main__':

		"""
		test
		1. class Device, buffer setter
			* [Success]	assign buf with different type compared to dict
			* [Success]	assign buf in dict type but with unnecessary key except 'U' and 'D'
			* [Success]	assign buf in dict type but with incorrect type of value compared to int
		2. class Device, status setter
			* [Success]	assign status with others type except str
			* [Success]	assign status with 'u' or 'd'
			* [Success]	assign status with others letter except 'U' or 'D'
		3. class Device, lambd setter
			* [Success]	assign lambd with non-integer value
		4. class UE, parentDevice setter
			* [Success]	assign parentDevice with the non-RN object
			* [Success]	assign parentDevice with RN class rather than instance
		5. class RN, RUE setter
			* [Success]	assign RUE with non-list object
			* [Success]	assign RUE with a list of non-UE object
			* [Success]	assign RUE with UE class object
			* [Failed]	assign by .append()
		"""

		print("Test\t\tprop/func\t\t\tresult")
		test_D = Device()
		test_UE = UE()
		test_RN = RN()
		print("====\t\t========\t\t\t========")
		print("Device\t\ttype(buf) is int\t\t", end='')
		test_D.buf = 100
		print("Device\t\tbuf={'U':50, 'D':100, 'Q':3}\t", end='')
		test_D.buf = {'U': 50, 'D': 100, 'Q': 3}
		print(test_D.buf)
		print("Device\t\tbuf={'U':20, 'D':100, 'Q':3}\t", end='')
		test_D.buf = {'U': 20, 'D': 100, 'Q': 3}
		print(test_D.buf)
		print("Device\t\tstatus=None\t\t\t", end='')
		test_D.status = None
		print("Device\t\tstatus='d'\t\t\t", end='')
		test_D.status = 'd'
		print(test_D.status)
		print("Device\t\tstatus='XD'\t\t\t", end='')
		test_D.status = 'XD'
		print("Device\t\tlambd='100'\t\t\t", end="")
		test_D.lambd = '100'
		print("----\t\t--------\t\t\t--------")
		print("UE\t\tparentDevice=None\t\t", end="")
		test_UE.parentDevice = None
		print("UE\t\tparentDevice=RN()\t\t", end="")
		test_UE.parentDevice = RN
		print("----\t\t--------\t\t\t--------")
		print("RN\t\tRUE={}\t\t\t\t", end="")
		test_RN.RUE = {}
		print("RN\t\tRUE=[1,2,3]\t\t\t", end="")
		test_RN.RUE = [1, 2, 3]
		print("RN\t\tRUE=[UE1, UE]\t\t\t", end="")
		test_RN.RUE = [test_UE, UE]
		print("RN\t\tRUE=[UE1], RUE.append(UE)\t", end="")  # FIXME
		test_RN.RUE = [test_UE]
		test_RN.RUE.append(UE)
		checkType = True
		for i in test_RN.RUE:
				if inspect.isclass(i):
					checkType = False
					break
		print(test_RN.RUE) if checkType else print(checkType)
