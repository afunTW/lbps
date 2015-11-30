class Customer:
	def __init__(self, arrival_time, service_start_time, service_time):
		self.arrival_time = arrival_time;
		self.service_start_time = service_start_time;
		self.service_time = service_time;
		self.service_end_time = self.service_start_time + self.service_time;
		self.wait = self.service_start_time + self.arrival_time;

#if __name__ == "__main__":
