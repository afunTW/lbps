# -*- coding: utf-8 -*-
#!/usr/bin/python

from math import exp, pow, factorial

class Poisson:
	def __init__(self, lambd, T, bufSize=1000):
		self.__lambd = lambd;
		self.__timeInterval = T;
		self.__bufSize = bufSize;	# represent as the number of packet 
	
	# property
	@property
	def lambd(self):
		return self.__lambd;
	
	@property
	def timeInterval(self):
		return self.__timeInterval;
	
	@property
	def bufSize(self):
		return self.__bufSize;
	
	# setter
	@lambd.setter
	def lambd(self, lambd):
		self.__lambd = lambd;
	
	@timeInterval.setter
	def timeInterval(self, T):
		self.__timeInterval = T;
	
	@bufSize.setter
	def bufSize(self, bufSize):
		self.__bufSize = bufSize;
	
	# classmethod
	# calc the prob that i-th packet accumulate in T ms under/over threshold
	@classmethod
	def Prob_AccDataUnderTH(cls, threshold, lambd, time):
		p_accumulate = 0;
		while(threshold >= 0):
			p_accumulate += exp((-1)*lambd*time)*pow(lambd*time, threshold)/factorial(threshold);
			threshold -= 1;
		return p_accumulate;
	
	@classmethod
	def Prob_AccDataOverTH(cls, threshold, lambd, time):
		return 1-Prob_AccDataUnderTH(threshold, lambd, time);

	# normal function
	# given lambd, DATA_TH, PROB_TH -> calc awake-sleep-cycle, K (TTI)
	def LengthAwkSlpCyl(self, DATA_TH=0.8, PROB_TH=0.8):
		K = 1;
		while(1):
			p_acc = Prob_AccDataOverTH(self.__bufSize*DATA_TH, self.__lambd, K);
			if(p_acc > PROB_TH): break;
			else: K+=1;
		return K
	
	# given lambd, awake-sleep-cycle, PROB_TH -> calc data accumulation, DataAcc (#packet)
	def DataAcc(self, K, PROB_TH=0.8):
		pkt=0;
		while(1):
			p_acc = Prob_AccDataUnderTH(pkt, self.__lambd, K);
			if(p_acc > PROB_TH): break;
			else: pkt+=1;
		return pkt;
