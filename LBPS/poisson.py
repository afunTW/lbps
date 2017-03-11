#!/usr/bin/python3

from math import exp, pow, factorial
from viewer import *

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
	threshold= int(threshold) if type(threshold) is float else threshold
	p_accumulate = 0

	while threshold >= 0:

		# p_accumulate += exp(-1*lambd*time)*pow(lambd*time, threshold)/factorial(threshold);
		tmp_p = exp(-1*lambd*simTime)

		# bug: exp value may too small to calc
		if tmp_p<=0:
			msg_warning("exp value is too small to calculate")
			return

		for i in range(1, threshold+1):
			tmp_p *= lambd*simTime/i

		p_accumulate += tmp_p;
		threshold -= 1

	# print("-	p_accumulate: %g" % p_accumulate)
	return p_accumulate

def Prob_AccDataOverTH(lambd, threshold, simTime):
	prob = Prob_AccDataUnderTH(lambd, threshold, simTime)
	return 1-prob if prob else 1

def LengthAwkSlpCyl(lambd, DATA_TH, PROB_TH= 0.8):

	# print("Calculating awake-sleep-cycle with DATA_TH(%d pkt), PROB_TH(%.2f)" % (DATA_TH, PROB_TH));
	K= 1			# ms

	while True:

		p_acc= Prob_AccDataOverTH(lambd, DATA_TH, K)
		# print("Get	prob: %f in %d TTI" % (p_acc, K))

		if p_acc > PROB_TH:
			break

		K+=1

	return K

def DataAcc(lambd, K, PROB_TH= 0.8):

	# print("Calculating number of packet accumulate in %d TTI with lambd %g (packet/ms)" %(K, lambd))
	pkt=0			# number of packet

	while True:

		p_acc= Prob_AccDataUnderTH(lambd, pkt, K)
		# print("Get	prob: %f in %d TTI only accumulate %d packet" % (p_acc, K, pkt))

		if not p_acc:
			msg_warning("exp value is too small to calculate")
			return

		if p_acc > PROB_TH:
			break

		pkt+= 1;

	return pkt;

def getDataTH(capacity, pkt_size, percent=0.8):
	return (capacity/pkt_size)*percent

if __name__ == "__main__":

	# For same UE, larger PROB_TH leads to larger K value
	# Fake UE info:
	#	bufSize= 8000 bits
	# 	lambd= (50 bit/ms) / pktSize (800 bits)
	#	DATA_TH= int(testUE.buf[testUE.status] * 0.8 / pktSize)= int(6400/800) = 8
	#	PROB_TH1= 0.8, PROB_TH2= 0.2
	lambd=50/800
	Data_TH=8
	P1=0.8
	P2=0.2

	K_star = LengthAwkSlpCyl(lambd, Data_TH, P1, True)
	K_caret = LengthAwkSlpCyl(lambd, Data_TH, P2, True)
	# K_caret = DataAcc(lambd, max(K_star), P1, True)

	print(max(K_star))
	print(max(K_caret))

	# plt.figure(1);
	# plt.title("Distribution of K_star and K_caret");
	# plt.xlabel("K(TTI)");
	# plt.ylabel("P");
	# plt.plot(sorted(K_star.keys()), sorted(K_star.values()), color= 'red');
	# plt.plot(sorted(K_caret.keys()), sorted(K_caret.values()), color= 'blue');
	# plt.grid(True);
	# plt.show()
