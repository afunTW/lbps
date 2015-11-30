__metaclass__=type
import random
import csv

class Customer:
  def __init__(self, arrival_time, service_start_time, service_time):
    self.arrival_time = arrival_time;
    self.service_start_time = service_start_time;
    self.service_time = service_time;
    self.service_end_time = self.service_start_time + self.service_time;
    self.wait = self.service_start_time + self.arrival_time;

"""
  @ brief: main func to simulate MM1 queueing
  @ para: 
  * lambd: inter arrival rate, it leads to arrival_time = lambd < 0 ? (negative infinity~0):(0~positive infinity)
  * mu: service rate
  * simulation_time: total simulation time
  @ return: none
"""
def QSim(lambd=False, mu=False, simulation_time=False):

  # input prompt
  if not lambd:
    lambd = input("Inter arrival rate: ");
  if not mu:
    mu = input("Service rate: ");
  if not simulation_time:
    simulation_time = input("Total simulation time: ");

  # Init clock, customer queue to hold data
  t=0;
  Customers=[];

  # run
  while t < simulation_time:
    
    # calc arrival rate for new customer
    if len(Customers) == 0:
      arrival_time = random.expovariate(lambd);
      service_start_time = arrival_time;
    else:
      arrival_time += random.expovariate(lambd);
      service_start_time = max(arrival_time, Customers[-1].service_end_time)

    # calc service rate for new customer
    service_time = random.expovariate(mu);

    # create new customer
    Customers.append(Customer(arrival_time, service_start_time, service_time));

    # increase clock until next end of service 
    t = arrival_time;

  # summary statistics
  waits = [a.wait for a in Customers];
  mean_wait = sum(waits)/len(waits);

  service_times = [a.service_time for a in Customers];
  mean_service_time = sum(service_times)/len(service_times);

  total_times = [waits[i] + service_times[i] for i in range(0, len(Customers))];
  mean_time = sum(total_times)/len(total_times);

  utilization = sum(service_times)/t;

  # output in terminal
  print "";
  print "Summary results:";
  print "";
  print "Number of customers: ",len(Customers);
  print "Mean Service Time: ",mean_service_time;
  print "Mean Wait: ",mean_wait;
  print "Mean Time in System: ",mean_time;
  print "Utilisation: ",utilization;
  print "";

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
