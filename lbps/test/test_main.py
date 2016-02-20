# -*- coding: utf-8 -*-
#!/usr/bin/python3

import __init__
from poisson import *
from device import Device, UE

"""
	@class init
	UE(buf={'U':0, 'D':0}, status='D', lambd=None, parentDevice = None)
	RN(buf={'U':0, 'D':0}, status='D', lambd=None, l_UE=None)

	@simulation para
	[int]	lambd: number of packet
	[int]	buffer size: bit
	[int]	packet size: bit
	[float]	DATA_TH: number of packet
	[float]	PROB_TH: probability threshold

	[int]	LengthAwkSlpCyl(lambd, DATA_TH, PROB_TH)
	[int]	DataAcc(lambd, K, PROB_TH)
"""
Llambd = 10;	# 10 bit/ms
Mlambd = 50;
Hlambd = 250;

SBufSize = {'D': 800};
LBufSize = {'D': 8000};

pktSize = 800;	# bits

if __name__ == '__main__':

	"""
		target: using const lambda to discuss the relation between K and DataAcc
	"""
	testUE= UE(LBufSize, 'D', Mlambd);	# buffer can store 10 pkt, need 16 TTI to transmit 1 pkt
	DATA_TH= int(testUE.buf[testUE.status] * 0.8 / pktSize);
	PROB_TH = 0.8;
	print("#	init")
	print(">	lambd means arrival rate: %g(bit/ ms), needs %d TTI to transmit 1 packet" % (testUE.lambd, pktSize/testUE.lambd))
	print(">	DATA_TH is accumulate %d packet by buffer size %d packet\n" % (DATA_TH, testUE.buf[testUE.status]/pktSize))

	K1= LengthAwkSlpCyl(testUE.lambd/pktSize , DATA_TH, PROB_TH)
	print(">	Get the K1= %d" % K1);

	# K2= K1
	# K2_DataAcc= DataAcc(testUE.lambd, K2, PROB_TH)
	# print(">	Accumulate Data in %d TTI: %d packet" % (K2, K2_DataAcc))
