#!/usr/bin/python3

from math import exp, pow, factorial

"""doc
	@method
	Prob_AccDataUnderTH:
		calculate the probability that i-th packet accumulate in T ms under threshold
	Prob_AccDataUnderTH:
		calculate the probability that i-th packet accumulate in T ms over threshold
	LengthAwkSlpCyl: calc awake-sleep-cycle, K (TTI)
	DataAcc: calc data accumulation, DataAcc (#packet)
"""
def Prob_AccDataUnderTH(lambd, threshold, simTime):
	p_accumulate = 0;
	while(threshold >= 0):
		# p_accumulate += exp(-1*lambd*time)*pow(lambd*time, threshold)/factorial(threshold);
		tmp_p = exp(-1*lambd*simTime);
		for i in range(1, threshold): tmp_p *= lambd*simTime/i;
		p_accumulate += tmp_p;
		threshold -= 1;
	return p_accumulate;

def Prob_AccDataOverTH(lambd, threshold, simTime):
	# print("Call	Prob_AccDataOverTH");
	return 1-Prob_AccDataUnderTH(lambd, threshold, simTime);

def LengthAwkSlpCyl(lambd, DATA_TH, PROB_TH=0.8):
	print("Calculating awake-sleep-cycle with DATA_TH(%d), PROB_TH(%.2f)" % (DATA_TH, PROB_TH));
	K = 1;
	while(1):
		p_acc= Prob_AccDataOverTH(lambd, DATA_TH, K);
		# print("Get	prob: %f" % p_acc)
		if(p_acc > PROB_TH): break;
		else: K+=1;
	return K

def DataAcc(lambd, K, PROB_TH=0.8):
	pkt=0;
	while(1):
		p_acc= Prob_AccDataUnderTH(lambd, pkt, K);
		if(p_acc > PROB_TH): break;
		else: pkt+=1;
	return pkt;
