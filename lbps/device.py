# -*- coding: utf-8 -*-
#!/usr/bin/python3

from poisson import Poisson

class Device:
	"""
		property:
		buf: buffer size
		status: point out the device is on upstream downstream by 'U' or 'D'
		process: using poisson only in this project
	"""
	def __init__(self):
		self._buf = 0;
		self._status = 'D';
		self._process = None;

	@property
	def buf(self):
		return self._buf;
	@buf.setter
	def buf(self, buf):
		self._buf = buf;
	
	@property
	def status(self):
		return self._status;
	@status.setter
	def status(self, status):
		self._status = status;
	
	@property
	def process(self):
		return self._process;
	@process.setter
	def process(self, proc):
		self._process = proc;
	
	"""
	@property
	def CQI(self):
		return self.__CQI;
	
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
	def __init__(self, lambd, buf=[0,0], status='D'):
		self.__lambd = lambd;
		self._process = Poisson(self.__lambd);
		self._buf = buf;
		self._status = status;
	
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
	def __init__(self, l_UE=None, buf=[0,0], status='D'):
		self.__RUE = l_UE;
		self.__lambd = None;
	
	@property
	def RUE(self):
		return self.__RUE;
	@RUE.setter
	def RUE(self, l_UE):
		self.__RUE = l_UE;
	
	@property
	def lambd(self):
		if self.__RUE is None:
			print("There's no served UEs for aggregate lambd");
			return None;
		else:
			return sum(ue.lambd for ue in self.__RUE);
	
	@property
	def process(self):
		if self.__lambd is None:
			print("There's no lambd for Poisson process");
			return None;
		else:
			return Poisson(self.__lambd);
