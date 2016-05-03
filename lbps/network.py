# -*- coding: utf-8 -*-
#!/usr/bin/python3

from config import traffic, DEVICE_CQI_TYPE

class Bearer(object):

	def __init__(self, D1, D2, status='D', interface='access', bandwidth=0, flow='VoIP'):
		self._D1 = D1
		self._D2 = D2
		self._status = status
		self._interface = interface
		self._bandwidth = bandwidth
		self._flow = flow if flow in traffic else None

	@property
	def D1(self):
		return self._D1;

	@property
	def D2(self):
		return self._D2;

	@property
	def status(self):
		return self._status;

	@status.setter
	def status(self, status):
		if type(status) is str and (status.upper() is 'U' or status.upper() is 'D'):
			self._status = status;

	@property
	def interface(self):
		return self._interface;

	@interface.setter
	def interface(self, interface):
		if type(interface) is str and (interface.lower() is 'access' or interface.lower() is 'backhaul'):
			self._interface = interface;

	@property
	def bandwidth(self):
		return self._bandwidth;

	@bandwidth.setter
	def bandwidth(self, bw):
		if type(bw) is int:
			self._bandwidth = bw;

	@property
	def flow(self):
		return self._flow;

def getCQIByType(CQI_type):
	"""[summary] mapping the CQI type to a list of CQI index

	[description] CQI_type
		L = 1-6
		M = 7-9
		H = 10-15

	Arguments:
		CQI_type {[type]} -- [description]

	Returns:
		[list] -- [mapping result, a list of CQI index]
	"""
	CQI_range = []

	if type(CQI_type) is not list or len(CQI_type) is 0:
		return

	for i in CQI_type:
		if i.upper() in DEVICE_CQI_TYPE:
			list(map(CQI_range.append, DEVICE_CQI_TYPE[i]))

	# remove duplicate value in list
	return list(set(CQI_range));
