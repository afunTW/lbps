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
	if type(threshold) is type(0.): threshold= int(threshold)
	p_accumulate = 0;
	while(threshold >= 0):
		# p_accumulate += exp(-1*lambd*time)*pow(lambd*time, threshold)/factorial(threshold);
		tmp_p = exp(-1*lambd*simTime);
		for i in range(1, threshold+1): tmp_p *= lambd*simTime/i;
		p_accumulate += tmp_p;
		threshold -= 1;
	# print("-	p_accumulate: %g" % p_accumulate)
	return p_accumulate;

def Prob_AccDataOverTH(lambd, threshold, simTime):
	return 1-Prob_AccDataUnderTH(lambd, threshold, simTime);

def LengthAwkSlpCyl(lambd, DATA_TH, PROB_TH= 0.8, view= None):
	print("...	Calculating awake-sleep-cycle with DATA_TH(%d), PROB_TH(%.2f)" % (DATA_TH, PROB_TH));
	K= 1;			# ms
	d_K= dict();	# {K: prob}
	while(1):
		p_acc= Prob_AccDataOverTH(lambd, DATA_TH, K);
		d_K[K]= p_acc;
		# print("Get	prob: %f in %d TTI" % (p_acc, K))

		if(p_acc > PROB_TH): break;
		else: K+=1;
	return d_K if view is True else K

def DataAcc(lambd, K, PROB_TH= 0.8, view= None):
	print("...	Calculating number of packet accumulate in %d TTI with lambd %g (packet/ms)" %(K, lambd))
	pkt=0;			# number of packet
	d_K= dict();	# {pkt: prob}
	while(1):
		p_acc= Prob_AccDataUnderTH(lambd, pkt, K);
		d_K[pkt]= p_acc;
		# print("Get	prob: %f in %d TTI only accumulate %d packet" % (p_acc, K, pkt))

		if(p_acc > PROB_TH): break;
		else: pkt+= 1;
	return d_K if view is True else pkt;

if __name__ == "__main__":

	# For same UE, larger PROB_TH leads to larger K value
	# Fake UE info:
	#	bufSize= 8000 bits
	# 	lambd= (50 bit/ms) / pktSize (800 bits)
	#	DATA_TH= int(testUE.buf[testUE.status] * 0.8 / pktSize)= int(6400/800) = 8
	#	PROB_TH1= 0.8, PROB_TH2= 0.2

	print("\tPROB_TH1 (0.51): " + str(sorted(LengthAwkSlpCyl(50/800, 8, 0.51, True).keys())[-1]))
	print("\tPROB_TH2 (0.5): " + str(sorted(LengthAwkSlpCyl(50/800, 8, 0.5, True).keys())[-1]))
