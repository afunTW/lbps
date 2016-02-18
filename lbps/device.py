# -*- coding: utf-8 -*-
#!/usr/bin/python3

from poisson import Poisson

class Device(object):
	"""
		property:
		[protected]	buf: buffer size (bits)
		[protected]	status: point out the device is on upstream downstream by 'U' or 'D'
		[protected]	lambd: data rate (bps)
	"""
	# def __init__(self):
	# 	self._buf = {'U':0, 'D':0};
	# 	self._status = 'D';

	@property
	def buf(self):
		return self._buf;
	@buf.setter
	def buf(self, buf):
		# pick the right key and value
		buf = {k:v for k,v in buf.items() if k is 'U' or k is 'D'}
		buf = {k:v for k,v in buf.items() if type(v) is type(1)}
		self._buf.update(buf);

	@property
	def status(self):
		return self._status;
	@status.setter
	def status(self, status):
		if status not 'D' or status not 'U':
			raise Exception("status value sould be 'D' or 'U'");
		self._status = status;

	# FIXME: need to consider more situation for data format and exception handling
	@property
	def lambd(self):
		return self._lambd;
	@lambd.setter
	def lambd(self, lambd):
		self._lambd = lambd;

class UE(Device):
	"""
	@property
	[protected]	buf[2]
	[protected]	status
	[protected]	lambd
	[private]	parentDevice: identity served RN
	"""
	def __init__(self, buf={'U':0, 'D':0}, status='D', lambd=None, parentDevice = None):
		self._buf = buf;
		self._status = status;
		self._lambd = lambd;
		self.__parentDevice = parentDevice;

	# FIXME: need to consider more situation for data format and exception handling
	@property
	def parentDevice(self):
		return self.__parentDevice;
	# should parent RN changable? or init in begining?
	@parentDevice.setter(self, pD):
		self.__parentDevice = pD;

class RN(Device):
	"""
	@property
	[protected]	buf[2]
	[protected]	status
	[protected]	lambd
	[private]	l_UE: a list of served UE
	"""
	# FIXME
	def __init__(self, buf={'U':0, 'D':0}, status='D', lambd=None, l_UE=None):
		self._buf = buf;
		self._status = status;
		self._lambd = None;
		self.__l_UE = l_UE;

	@property
	def l_UE(self):
		return self.__l_UE;
	@l_UE.setter
	def l_UE(self, l_UE):
		if type(l_UE) != list or type(l_UE[0]) != UE:
			raise Exception("Wrong type: " + str(l_UE));
		self.__l_UE = l_UE;
		setattr(self, '__lambd')

	# rewrite lambd method, cause RN's lambd is equal to aggregate RUE lambd
	@property
	def lambd(self):
		return self.__lambd;
	@lambd.setter
	def lambd(self):
		if self.__l_UE is None:
			print("There's no served UEs for aggregate lambd");
		self.__lambd = sum(ue.lambd for ue in self.__l_UE);
		setattr(self, '_process')
