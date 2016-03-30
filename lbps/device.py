# -*- coding: utf-8 -*-
#!/usr/bin/python3

import inspect
import random
from network import Channel
from config import DEVICE_CQI_TYPE, traffic

def raiser(err): raise err if type(err) is Exception else raiser(Exception(str(err)))

class Device(Channel):
	def __init__(self, buf={}, status='D', link='access', bandwidth=0, CQI=0, flow='VoIP'):
		"""
		property:
		[protected]	buf: buffer size (bits)
		[protected]	status: identify the device is on upstream downstream by 'U' or 'D'
		[protected]	link: identify the link is backhaul or access
		[protected]	lambd: data rate (bps)
		"""
		self._buf = buf;
		self._status = status;
		self._link = Channel(link, bandwidth, CQI, flow);
		self._lambd = self._link.bitrate/self._link.pkt_size;

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

	@property
	def link(self):
		return self._link;

	def isDevice(testDevice, targetClass):
		return True if isinstance(testDevice, targetClass) else False;

class UE(Device):
	# def __init__(self, buf={}, status='D', link='access', bandwidth=0, CQI=0, flow='VoIP', parent=None):
	def __init__(self, buf={}, status='D', parent=None):
		"""
		@property
		[protected]	buf
		[protected]	status
		[protected]	link
		[protected]	lambd
		[private]	parent: identity served RN
		"""
		self._buf = buf;
		self._status = status;
		# self._link = Channel(link, bandwidth, CQI, flow);
		# self._lambd = self._link.bitrate/self._link.pkt_size;
		self.__parent = parent;

	@property
	def parent(self):
		return self.__parent;
	@parent.setter
	def parent(self, pD):
		try:
			self.__parentDevice = pD if UE.isDevice(pD, RN) else raiser(Exception("parent should be type of RN instance"));
		except Exception as e:
			print(e)

class RN(Device):
	def __init__(self, buf={}, status='D', link='access', bandwidth=0, CQI=0, flow='VoIP',RUE=[]):
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
		self._link = Channel(link, bandwidth, CQI, flow);
		self._lambd = 0;
		self.__RUE = RUE;

	@property
	def RUE(self):
		return self.__RUE;
	@RUE.setter
	def RUE(self, RUE):
		"""
		check the type of RUE is a list and each element is type of UE
		set the RN lambda, which is aggregate RUE lambda

		NOTE: setting _lambd in this setter rather then lambd.setter to prevent from changing value directly
		# FIXME: append() would pass any value
		"""
		try:
			RUE = list(RUE) if RUE is not list else RUE;
			check = list(map(lambda x: RN.isDevice(x, UE), RUE));
			if all(check):
				self.__RUE = RUE;
				self._lambd = sum(ue.lambd for ue in self.__RUE);
			else:
				raise Exception("RUE should be all UE instance object");
		except Exception as e:
			print(e);

	def add_UE(self, count, CQI_type, buf={}, status='D', link='access', bandwidth=0, flow='VoIP'):
		"""
		this function will add multiple UEs and assign to RN.RUE

		@parameter
		    count: number of UE will be created
			CQI_type: ['L','M','H'] which is L=CQI(1-6), M=CQI(7-9), H=CQI(10-15)
		"""
		CQI_range = [];

        # check the para value and append to a list
		if type(count) is not int or count is 0:
			return;
		else:
			for i in CQI_type:
				i = i.upper();
				if i in DEVICE_CQI_TYPE:
					list(map(CQI_range.append, DEVICE_CQI_TYPE[i]));

		# remove duplicate value in list
		CQI_range = list(set(CQI_range))

		# randomly choose a CQI value from CQI_range and assign to RUE list
		self.RUE = [UE(buf=buf, status=status, link=link, bandwidth=bandwidth, \
			CQI=random.choice(CQI_range), flow=flow, parent=self) for i in range(count)];

class eNB(Device):
	def __init__(self, buf={}, status='D', link='access', bandwidth=0, CQI=0, flow='VoIP',relays=[]):
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
		self._link = Channel(link, bandwidth, CQI);
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
