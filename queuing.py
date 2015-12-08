# -*- coding:utf8  -*-
__metaclass__=type
#import csv
import random
import matplotlib.pyplot as plt
from component import Customer

class queuing:
	def __init__(self, lambd, mu, simulation_time):
		self.__lambd = lambd;
		self.__mu = mu;
		self.__simulation_time = simulation_time;
		self.__Customers = [];
		self.__mean_wait = False;
		self.__Poisson = False;
		self.__mean_service_time = False;
		self.__mean_time = False;
		self.__utilization = False;

	@property
	def lambd(self):
		return self.__lambd;
	@lambd.setter
	def lambd(self, lambd):
		self.__lambd = lambd;
	@property
	def mu(self):
		return self.__mu;
	@mu.setter
	def mu(self, mu):
		self.__mu = mu;
	@property
	def simulation_time(self):
		return self.__simulation_time;
	@simulation_time.setter
	def simulation_time(self, t):
		self.__simulation_time = t;

	@property
	def Poisson(self):
		return self.__Poisson;
	@property
	def Customers(self):
		return self.__Customers;
	@property
	def served_customer(self):
		return len(self.__Customers);
	@property
	def mean_wait(self):
		return self.__mean_wait;
	@property
	def mean_service_time(self):
		return self.__mean_service_time;
	@property
	def mean_time(self):
		return self.__mean_time;
	@property
	def utilization(self):
		return self.__utilization;

	def MM1(self):
		t=0;
		self.__Customers = [];
		while t < self.__simulation_time:
			if len(self.__Customers) == 0:
				arrival_time = random.expovariate(self.__lambd);
				service_start_time = arrival_time;
			else:
				arrival_time += random.expovariate(self.__lambd);
				service_start_time = max(arrival_time, self.__Customers[-1].service_end_time)

			service_time = random.expovariate(self.__mu);
			self.__Customers.append(Customer(arrival_time, service_start_time, service_time));
			t = arrival_time;
		self.__Poisson = "MM1";
		self.collect_data();

	def MM2(self):
		t=0;
		arrival_time = 0;
		self.__Customers = [];
		while t < self.__simulation_time:
			arrival_time += random.expovariate(self.__lambd);
			if len(self.__Customers) == 0 or len(self.__Customers) == 1:
				service_start_time = arrival_time;
			else:
				service_start_time = max(arrival_time, self.__Customers[-1].service_end_time, self.__Customers[-2].service_end_time)

			service_time = random.expovariate(self.__mu);
			self.__Customers.append(Customer(arrival_time, service_start_time, service_time));
			t = arrival_time;
		self.__Poisson = "MM2";
		self.collect_data();

	def collect_data(self):
		waits = [a.wait for a in self.__Customers];
		self.__mean_wait = sum(waits)/len(waits);
		service_times = [a.service_time for a in self.__Customers];
		self.__mean_service_time = sum(service_times)/len(service_times);
		total_times = [waits[i] + service_times[i] for i in range(0, len(self.__Customers))];
		self.__mean_time = sum(total_times)/len(total_times);
		self.__utilization = sum(service_times) / self.__Customers[-1].arrival_time;

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
	plt.ylim(0,20);

	ana_x = [i/1000. for i in xrange(1, 1000, 1)];
	ana_MM1_y = [1/(1.0-i) for i in ana_x];
	ana_MM2_y = [1/(1.0-(i*i)) for i in ana_x];
	plt.plot(ana_x, ana_MM1_y, color='red', label='$AnalyticMM1$');
	plt.plot(ana_x, ana_MM2_y, color='blue', label='$AnalyticMM2$');


	# MM1
	test = queuing(1,1,1000000);
	test.MM1();
	test_MM1_y = [(1/test.mean_service_time) / (1-i) for i in lambd];
	plt.plot(lambd, test_MM1_y, color='red', ls='dashed', label='$MM1$', marker='x');

	# MM2
	test.MM2();
	test_MM2_y = [(1/test.mean_service_time) / (1-(i*i)) for i in lambd];
	plt.plot(lambd, test_MM2_y, color='blue', ls='dotted', label='$MM2$', marker='x');

	# show
	plt.legend();
	plt.show();
