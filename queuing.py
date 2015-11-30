__metaclass__=type
import random
import csv
from component import Customer

def show_queuing_result(Customers):

	waits = [a.wait for a in Customers];
	mean_wait = sum(waits)/len(waits);
	service_times = [a.service_time for a in Customers];
	mean_service_time = sum(service_times)/len(service_times);
	total_times = [waits[i] + service_times[i] for i in range(0, len(Customers))];
	mean_time = sum(total_times)/len(total_times);
	utilization = sum(service_times)/Customers[-1].arrival_time;

	print "\nSummary results:\n";
	print "Number of served customers: ", len(Customers);
	print "Mean Service Time: ", mean_service_time;
	print "Mean Wait: ", mean_wait;
	print "Mean Time in System: ", mean_time;
	print "Utilisation: ", utilization;

"""
	# output as csv file
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
"""

def MM1(lambd=False, mu=False, simulation_time=False):
	
	if not lambd:
		lambd = input("Inter arrival rate: ");
	if not mu:
		mu = input("Service rate: ");
	if not simulation_time:
		simulation_time = input("Total simulation time: ");

	t=0;
	Customers=[];

	# run
	while t < simulation_time:
		if len(Customers) == 0:
			arrival_time = random.expovariate(lambd);
			service_start_time = arrival_time;
		else:
			arrival_time += random.expovariate(lambd);
			service_start_time = max(arrival_time, Customers[-1].service_end_time)

		service_time = random.expovariate(mu);
		Customers.append(Customer(arrival_time, service_start_time, service_time));
		t = arrival_time;
	
	show_queuing_result(Customers);

def MM2(lambd=False, mu=False, simulation_time=False):
	
	if not lambd:
		lambd = input("Inter arrival rate: ");
	if not mu:
		mu = input("Service rate: ");
	if not simulation_time:
		simulation_time = input("Total simulation time: ");

	t=0;
	arrival_time = 0;
	Customers=[];

	# run
	while t < simulation_time:
		arrival_time += random.expovariate(lambd);

		if len(Customers) == 0 or len(Customers) == 1:
			service_start_time = arrival_time;
		else:
			service_start_time = max(arrival_time, Customers[-1].service_end_time, Customers[-2].service_end_time)

		service_time = random.expovariate(mu);
		Customers.append(Customer(arrival_time, service_start_time, service_time));
		t = arrival_time;
	
	show_queuing_result(Customers);

if __name__ == "__main__":
	lambd = [ i/10. for i in xrange(1, 10, 1)];
	lambd.append(0.95);
