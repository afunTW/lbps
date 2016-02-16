# -*- coding: utf-8 -*-
#!/usr/bin/python3

from math import exp, pow, factorial

class Poisson:
	"""
	@property
	lambd: data rate
	timeInterval: how long would the process take?

	@classmethod
	Prob_AccDataUnderTH: 
		calculate the probability that i-th packet accumulate in T ms under threshold
	Prob_AccDataUnderTH:
		calculate the probability that i-th packet accumulate in T ms over threshold

	@method
	LengthAwkSlpCyl: calc awake-sleep-cycle, K (TTI)
	DataAcc: calc data accumulation, DataAcc (#packet)
	"""
	def __init__(self, lambd, T=0):
		self.__lambd = lambd;
		self.__timeInterval = T;
		print("create: \t" + self.__str__());
	
	def __str__(self):
		return "Poisson(lambd= " + str(self.__lambd) + ", timeInterval= " + str(self.__timeInterval) + " )";

	@property
	def lambd(self):
		return self.__lambd;
	@lambd.setter
	def lambd(self, lambd):
		self.__lambd = lambd;
	
	@property
	def timeInterval(self):
		return self.__timeInterval;
	@timeInterval.setter
	def timeInterval(self, T):
		self.__timeInterval = T;
		print("set time: \t" + self.__str__());
	
	@classmethod
	def Prob_AccDataUnderTH(cls, threshold, lambd, time):
		p_accumulate = 0;
		while(threshold >= 0):
			"""
			print("exp:\t\t" + str(exp((-1)*lambd*time)))
			print("lambd: \t\t" + str(lambd))
			print("time: \t\t" + str(time))
			print("threshold: \t" + str(threshold))
			print("pow: \t\t" + str(pow(lambd*time, threshold)))
			print("fractorial : \t" + str(factorial(threshold)))
			"""
			p_accumulate += exp(-1*lambd*time)*pow(lambd*time, threshold)/factorial(threshold);
			threshold -= 1;
		return p_accumulate;
	
	@classmethod
	def Prob_AccDataOverTH(cls, threshold, lambd, time):
		return 1-cls.Prob_AccDataUnderTH(threshold, lambd, time);

	# normal function
	# given lambd, DATA_TH, PROB_TH -> calc awake-sleep-cycle, K (TTI)
	def LengthAwkSlpCyl(self, DATA_TH, PROB_TH=0.8):
		K = 1;
		while(1):
			p_acc = self.Prob_AccDataOverTH(DATA_TH, self.__lambd, K);
			if(p_acc > PROB_TH): break;
			else: K+=1;
		return K
	
	# given lambd, awake-sleep-cycle, PROB_TH -> calc data accumulation, DataAcc (#packet)
	def DataAcc(self, K, PROB_TH=0.8):
		pkt=0;
		while(1):
			p_acc = self.Prob_AccDataUnderTH(pkt, self.__lambd, K);
			if(p_acc > PROB_TH): break;
			else: pkt+=1;
		return pkt;
