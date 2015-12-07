__metaclass__=type
#import csv
import random
import matplotlib.pyplot as plt
from component import Customer

class queuing:
	def __init__(self, lambd, mu, simulation_time):
		self._lambd = lambd;
		self._mu = mu;
		self._simulation_time = simulation_time;
		self._Customers = [];
		self._mean_wait = False;
		self._Poisson = False;
		self._mean_service_time = False;
		self._mean_time = False;
		self._utilization = False;

	@property
	def lambd(self):
		return self._lambd;
	@lambd.setter
	def lambd(self, lambd):
		self._lambd = lambd;
	@property
	def mu(self):
		return self._mu;
	@mu.setter
	def mu(self, mu):
		self._mu = mu;
	@property
	def simulation_time(self):
		return self._simulation_time;
	@simulation_time.setter
	def simulation_time(self, t):
		self._simulation_time = t;

	@property
	def Poisson(self):
		return self._Poisson;
	@property
	def Customers(self):
		return self._Customers;
	@property
	def served_customer(self):
		return len(self._Customers);
	@property
	def mean_wait(self):
		return self._mean_wait;
	@property
	def mean_service_time(self):
		return self._mean_service_time;
	@property
	def mean_time(self):
		return self._mean_time;
	@property
	def utilization(self):
		return self._utilization;

	def MM1(self):
		t=0;
		self._Customers = [];
		while t < self._simulation_time:
			if len(self._Customers) == 0:
				arrival_time = random.expovariate(self._lambd);
				service_start_time = arrival_time;
			else:
				arrival_time += random.expovariate(self._lambd);
				service_start_time = max(arrival_time, self._Customers[-1].service_end_time)

			service_time = random.expovariate(self._mu);
			self._Customers.append(Customer(arrival_time, service_start_time, service_time));
			t = arrival_time;
		self._Poisson = "MM1";
		self.collect_data();

	def MM2(self):
		t=0;
		arrival_time = 0;
		self._Customers = [];
		while t < self._simulation_time:
			arrival_time += random.expovariate(self._lambd);
			if len(self._Customers) == 0 or len(self._Customers) == 1:
				service_start_time = arrival_time;
			else:
				service_start_time = max(arrival_time, self._Customers[-1].service_end_time, self._Customers[-2].service_end_time)

			service_time = random.expovariate(self._mu);
			self._Customers.append(Customer(arrival_time, service_start_time, service_time));
			t = arrival_time;
		self._Poisson = "MM2";
		self.collect_data();

	def collect_data(self):
		waits = [a.wait for a in self._Customers];
		self._mean_wait = sum(waits)/len(waits);
		service_times = [a.service_time for a in self._Customers];
		self._mean_service_time = sum(service_times)/len(service_times);
		total_times = [waits[i] + service_times[i] for i in range(0, len(self._Customers))];
		self._mean_time = sum(total_times)/len(total_times);
		self._utilization = sum(service_times) / self._Customers[-1].arrival_time;

	def output_csv(self):
		if input("Output data to csv (True/False)? "):
			outfile = open("MM1(%s, %s, %s).csv" % (lambd, mu, simulation_time), "wb");
			output = csv.writer(outfile);
			output.writerow(['Customer','Arrival_Date','Wait','Service_Start_Date','Service_Time','Service_End_Date']);
			rowinfo = [[a.arrival_time, a.wait, a.service_start_time, a.service_time, a.service_end_time] for a in Customers];
			for i in range(0, len(Customers)):
				row = [i+1] + rowinfo[i];
				output.writerow(row);
			outfile.close();
		print ""
		return;

if __name__ == "__main__":
	lambd = [ i/10. for i in xrange(1, 10, 1)];
	lambd.append(0.95);

	plt.xlabel(u"\u03C1");
	plt.ylabel("T");
	plt.title("MM1 and MM2 simulation result");
	plt.xlim(0,1);
	plt.ylim(0,25);

	ana_x = [i/100. for i in xrange(1, 100, 1)];
	ana_y = [1/(1.0-i) for i in ana_x]
	plt.plot(ana_x, ana_y, color='black');

	# MM1
	test = queuing(1,1,1000000);
	test.MM1();
	test_MM1_y = [(1/test.mean_service_time) / (1-i) for i in lambd];
	plt.plot(lambd, test_MM1_y, color='red', ls='dashed', label='$MM1$');

	# MM2
	test.MM2();
	test_MM2_y = [(1/test.mean_service_time) / (2.0*(1-i)) for i in lambd];
	plt.plot(lambd, test_MM2_y, color='blue', ls='dotted', label='$MM2$');

	# show
	plt.legend();
	plt.show();
