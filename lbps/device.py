# -*- coding: utf-8 -*-
#!/usr/bin/python3

import inspect
from network import Channel

def raiser(err): raise err if type(err) is Exception else raiser(Exception(str(err)))

class Device(Channel):
	def __init__(self, buf={}, status='D', lambd=0, link='access', bandwidth=0, CQI=0):
		"""
		property:
		[protected]	buf: buffer size (bits)
		[protected]	status: identify the device is on upstream downstream by 'U' or 'D'
		[protected]	link: identify the link is backhaul or access
		[protected]	lambd: data rate (bps)
		"""
		self._buf = buf;
		self._status = status;
		self._lambd = lambd;
		self._link = link;
		self._bandwidth = bandwidth;
		self._CQI = CQI;

	@property
	def buf(self):
		return self._buf;
	@buf.setter
	def buf(self, buf):
		"""
		buffer filter by checking type, key and value first, then update
		maintain the buffer always have only two items with key 'U' and 'D'
		and the value are always type int as well
		"""
		try:
			if type(buf) is dict:
				buf = {k:v for k,v in buf.items() if k is 'U' or k is 'D'}
				buf = {k:v for k,v in buf.items() if type(v) is int}
				self._buf.update(buf);
			else:
				raise Exception("Buffer should be the type of dict.");
		except Exception as e:
			print(e);

	@property
	def status(self):
		return self._status;
	@status.setter
	def status(self, status):
		"""
		maintain status will only in the value of 'U' or 'D'
		"""
		try:
			if type(status) is str and (status.upper() is 'U' or status.upper() is 'D'):
				self._status = status;
			else:
				raise Exception("status value sould be str and the value should be 'U' or 'D'");
		except Exception as e:
			print(e);

	@property
	def lambd(self):
		return self._lambd;
	@lambd.setter
	def lambd(self, lambd):
		try:
			self._lambd = lambd if type(lambd) is int else raiser(Exception("lambd value should be int"));
		except Exception as e:
			print(e)

class UE(Device):
	def __init__(self, buf={}, status='D', lambd=0, bandwidth=0, CQI=0, parentDevice= None):
		"""
		@property
		[protected]	buf
		[protected]	status
		[protected]	link
		[protected]	lambd
		[private]	parentDevice: identity served RN
		"""
		self._buf = buf;
		self._status = status;
		self._link = 'access';
		self._lambd = lambd;
		self._bandwidth = bandwidth;
		self._CQI = CQI;
		self.__parentDevice = parentDevice;

	@property
	def parentDevice(self):
		return self.__parentDevice;
	@parentDevice.setter
	def parentDevice(self, pD):
		"""
		parent should be the type of RN object
		check the type and make sure its instance rather than class by isinstance(obj, '__class__') build-in function
		"""
		try:
			self.__parentDevice = pD if isinstance(pD, RN) and not inspect.isclass(pD) else raiser(Exception("parent should be type of RN instance"));
		except Exception as e:
			print(e)

class RN(Device):
	def __init__(self, buf={}, status='D', bandwidth=0, CQI=0, RUE=[]):
		"""
		@property
		[protected]	buf
		[protected]	status
		[protected]	link
		[protected]	lambd
		[private]	RUE: a list of served UE
		"""
		self._buf = buf;
		self._status = status;
		self._link = 'backhaul';
		self._lambd = 0;
		self._bandwidth = bandwidth;
		self._CQI = CQI;
		self.__RUE = RUE;

	@property
	def RUE(self):
		return self.__RUE;
	@RUE.setter
	def RUE(self, RUE):
		"""
		check the type of RUE is a list and each element is type of UE
		set the RN lambda, which is aggregate RUE lambda

		NOTE: setting lambda in this setter rather then lambd.setter to prevent from changing value directly
		# FIXME: append() would pass any value
		"""
		try:
			if type(RUE) is list:
				for i in RUE:
					if not isinstance(i, UE) or inspect.isclass(i):
						raise Exception("RUE should be all UE instance object");

				self.__RUE = RUE;
				self._lambd = sum(ue.lambd for ue in self.__RUE);
			else:
				raise Exception("RUE should be the type of list")
		except Exception as e:
			print(e);

class eNB(Device):
	def __init__(self, buf={}, status='D', relays=None):
		"""
		@property
		[protected]	buf
		[protected]	status
		[protected]	link
		[protected]	lambd
		[private]	relays: a list of served RN
		"""
		self._buf = buf;
		self._status = status;
		self._link = 'backhaul';
		self._lambd = 0;
		self.__relays = relay;

	@property
	def relays(self):
		return self.__relays;
	@relays.setter
	def relays(self, relays):
		"""
		similar to RN.RUE setter
		"""
		try:
			if type(relays) is list:
				for i in relays:
					if not isinstance(i, RN) or inspect.isclass(i):
						raise Exception("relays should be all RN instance object");
				self.__relays = relays;
				self._lambd = sum(rn.lambd for rn in self.__relays);
			else:
				raise Exception("relays should be the type of list")
		except Exception as e:
			print(e);

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
	test_D = Device();
	test_UE = UE();
	test_RN = RN()
	print("====\t\t========\t\t\t========")
	print("Device\t\ttype(buf) is int\t\t", end='');
	test_D.buf = 100;
	print("Device\t\tbuf={'U':50, 'D':100, 'Q':3}\t", end='');
	test_D.buf = {'U':50, 'D':100, 'Q':3}
	print(test_D.buf)
	print("Device\t\tbuf={'U':20, 'D':100, 'Q':3}\t", end='');
	test_D.buf = {'U':20, 'D':100, 'Q':3}
	print(test_D.buf)
	print("Device\t\tstatus=None\t\t\t", end='');
	test_D.status = None;
	print("Device\t\tstatus='d'\t\t\t", end='');
	test_D.status = 'd';
	print(test_D.status)
	print("Device\t\tstatus='XD'\t\t\t", end='');
	test_D.status = 'XD';
	print("Device\t\tlambd='100'\t\t\t", end="");
	test_D.lambd='100';
	print("----\t\t--------\t\t\t--------")
	print("UE\t\tparentDevice=None\t\t", end="");
	test_UE.parentDevice = None;
	print("UE\t\tparentDevice=RN()\t\t", end="");
	test_UE.parentDevice = RN;
	print("----\t\t--------\t\t\t--------")
	print("RN\t\tRUE={}\t\t\t\t", end="")
	test_RN.RUE = {};
	print("RN\t\tRUE=[1,2,3]\t\t\t", end="")
	test_RN.RUE = [1,2,3];
	print("RN\t\tRUE=[UE1, UE]\t\t\t", end="")
	test_RN.RUE = [test_UE, UE];
	print("RN\t\tRUE=[UE1], RUE.append(UE)\t", end="");	# FIXME
	test_RN.RUE = [test_UE];
	test_RN.RUE.append(UE);
	checkType = True;
	for i in test_RN.RUE:
		if inspect.isclass(i): checkType=False;break;
	print(test_RN.RUE) if checkType else print(checkType);
