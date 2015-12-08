class Customer:
	def __init__(self, arrival_time, service_start_time, service_time):
		self._arrival_time = arrival_time;
		self._service_start_time = service_start_time;
		self._service_time = service_time;
		self._service_end_time = self.service_start_time + self.service_time;
		self._wait = self.service_start_time + self.arrival_time;

		@property
		def arrival_time(self):
			return self._arrival_time;
		@arrival_time.setter
		def arrival_time(self, at):
			self._arrival_time = at;
		@property
		def service_start_time(self):
			return self._service_start_time;
		@service_start_time.setter
		def service_start_time(self, sst):
			self._service_start_time = sst;
		@property
		def service_time(self):
			return self._service_time;
		@service_time.setter
		def service_time(self, st):
			self._service_time = st;

		@property
		def service_end_time(self):
			return self._service_end_time;
		@property
		def wait(self):
			return self._wait;

#if __name__ == "__main__":
