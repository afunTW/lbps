# -*- coding: utf-8 -*-
#!/usr/bin/python3

from poisson import Poisson

class Device(object):
	"""
		property:
		buf: buffer size
		status: point out the device is on upstream downstream by 'U' or 'D'
		process: using poisson only in this project
	"""
	def __init__(self):
		self._buf = {'U':0, 'D':0};
		self._status = 'D';
		self._process = None;

	@property
	def buf(self):
		return self._buf;
	@buf.setter
	def buf(self, buf):
		if dict.get('D') is None or dict.get('U') is None:
			raise Exception("Buffer shold be a dict with pair ('D': [int]) and ('U': [int])");
		self._buf = buf;
	
	@property
	def status(self):
		return self._status;
	@status.setter
	def status(self, status):
		if status not 'D' or atatus not 'U':
			raise Exception("status value sould be 'D' or 'U'");
		self._status = status;
	
	@property
	def process(self):
		return self._process;
	@process.setter
	def process(self, proc):
		self._process = proc;
	
	"""
	@property
	def totalAwkTime(self):
		return self.__totalAwkTime;
	
	@property
	def delayBudget(self):
		return self.__delayBudget;

	@property
	def pktArrive(self):
		return self.__pktArrive;

	@property
	def pktDiscard(self):
		return self.__pktDiscard;
	"""

class UE(Device):
	"""
	@property
	lambd: data rate
	buf[2]: buffer size for upstream/downstream (from Device)
	status: upstream/downstream (from Device)
	process: binding Poisson (from Device)
	"""
	# FIXME
	def __init__(self, lambd, buf=[0,0], status='D'):
		self.__lambd = lambd;
		self._process = Poisson(self.__lambd);
		self._buf = buf;
		self._status = status;
		self.targetDevice = None;
	
	@property
	def lambd(self):
		return self.__lambd;
	@lambd.setter
	def lambd(self, lambd):
		self.__lambd = lambd;

class RN(Device):
	"""
	@property
	RUE: a list of served UE
	lambd: aggregate the lambd from RUEs
	buf[2]: buffer size for upstream/downstream (from Device)
	status: upstream/downstream, could be different from UE (from Device)
	process: binding Poisson (from Device)
	"""
	# FIXME
	def __init__(self, l_UE=None, buf={'D':0, 'U':0}, status='D'):
		self.__l_UE = l_UE;
		self.__lambd = None;
		self._buf = buf;
		self._status = status;

	@property
	def l_UE(self):
		return self.__l_UE;
	@l_UE.setter
	def l_UE(self, l_UE):
		if type(l_UE) != list or type(l_UE[0]) != UE:
			raise Exception("Wrong type: " + str(l_UE));
		self.__l_UE = l_UE;
		setattr(self, '__lambd')

	@property
	def lambd(self):
		return self.__lambd;
	@lambd.setter
	def lambd(self):
		if self.__l_UE is None:
			print("There's no served UEs for aggregate lambd");
		self.__lambd = sum(ue.lambd for ue in self.__l_UE);
		setattr(self, '_process')
	
	@property
	def process(self):
		return self._process;
	@process.setter
	def process(self):
		if self.__lambd is None:
			print("There's no lambd for Poisson process");
		self._process = Poisson(self.__lambd);
