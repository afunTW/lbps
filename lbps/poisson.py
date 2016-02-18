# -*- coding: utf-8 -*-
#!/usr/bin/python3

from math import exp, pow, factorial

class Poisson(object):
	"""
	@classmethod
	Prob_AccDataUnderTH:
		calculate the probability that i-th packet accumulate in T ms under threshold
	Prob_AccDataUnderTH:
		calculate the probability that i-th packet accumulate in T ms over threshold

	@method
	LengthAwkSlpCyl: calc awake-sleep-cycle, K (TTI)
	DataAcc: calc data accumulation, DataAcc (#packet)
	"""
	@classmethod
	def Prob_AccDataUnderTH(cls, threshold, lambd, time):
		p_accumulate = 0;
		while(threshold >= 0):
			# p_accumulate += exp(-1*lambd*time)*pow(lambd*time, threshold)/factorial(threshold);
			tmp_p = exp(-1*lambd*time);
			for i in range(0, threshold):
				tmp_p *= lambd*time/i;
			p_accumulate += tmp_p;
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
