class Bearer(object):
	def __init__(self, src, dest, interface, bandwidth=0, flow='VoIP'):
		self.__source = src
		self.__destination = dest
		self.__interface = interface
		self.__bandwidth = bandwidth
		self.__flow = flow

	@property
	def source(self): return self.__source
	@property
	def destination(self): return self.__destination
	@property
	def interface(self): return self.__interface
	@property
	def bandwidth(self): return self.__bandwidth
	@property
	def flow(self): return self.__flow