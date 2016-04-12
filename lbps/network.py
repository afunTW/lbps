# -*- coding: utf-8 -*-
#!/usr/bin/python3

from config import traffic, DEVICE_CQI_TYPE

class Bearer(object):

	def __init__(self, src, dest, status='D', interface='access', bandwidth=0, CQI=0, flow='VoIP'):
		"""
		property:
		[protected] src: if the status is 'D' means the flow is from src to dest
		[protected] dest: if the status is 'U' means the flow is from dest to src
		[protected] status: identify the device is on upstream downstream by 'U' or 'D'
		[protected] interface: identify the link is 'backhaul' or 'access'
		[protected] bandwidth: for calculating the capacity of the link (MHz)
		[protected] CQI: identify the channel quality of the link
		[protected] flow: flow type
		"""
		self._src = src;
		self._dest = dest;
		self._status = status;
		self._interface = interface;
		self._bandwidth = bandwidth;
		self._CQI = CQI;

		if flow in traffic:
			self._flow = flow;
			self._bitrate = traffic[flow]['bitrate'];
			self._pkt_size = traffic[flow]['pkt_size'];
			self._delay_budget = traffic[flow]['delay_budget'];
		else:
			raise Exception(str(flow) + " doesn't defined");

	@property
	def src(self):
		return self._src;

	@property
	def dest(self):
		return self._dest;

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
				raise Exception(
						"status value sould be str and the value should be 'U' or 'D'");
		except Exception as e:
			print(e);

	@property
	def interface(self):
		return self._interface;
	@interface.setter
	def interface(self, interface):
		try:
			if type(interface) is str and (interface.lower() is 'access' or interface.lower() is 'backhaul'):
				self._interface = interface;
			else:
				raise Exception("link should be str type and the value is 'access' or 'backhaul'")
		except Exception as e:
			print(e)

	@property
	def bandwidth(self):
		return self._bandwidth;
	@bandwidth.setter
	def bandwidth(self, bw):
		try:
			if type(bw) is int:
				self._bandwidth = bw;
			else:
				raise Exception("bandwidth should be the type of int (MHz)")
		except Exception as e:
			print(e);

	@property
	def CQI(self):
		return self._CQI;
	@CQI.setter
	def CQI(self, CQI):
		try:
			if type(CQI) is int:
				self._CQI = CQI;
			else:
				raise Exception("CQI should be the type of int")
		except Exception as e:
			print(e);

	@property
	def flow(self):
		return self._flow;

	@property
	def bitrate(self):
		return self._bitrate;

	@property
	def pkt_size(self):
		return self._pkt_size;

	@property
	def delay_budget(self):
		return self._delay_budget;

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

	if type(CQI_type) is not list:
		print("network::getCQIByType\tgiven para is non-list type")
		return
	elif len(CQI_type) is 0:
		print("network::getCQIByType\tthe length of list less than 1")
		return
	else:
		for i in CQI_type:
			i = i.upper()
			if i in DEVICE_CQI_TYPE:
				list(map(CQI_range.append, DEVICE_CQI_TYPE[i]))

	# remove duplicate value in list
	return list(set(CQI_range));
