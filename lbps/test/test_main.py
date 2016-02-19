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
	[int]	lambd: bps
	[int]	buffer size: bit
	[int]	packet size: bit
	[float]	DATA_TH: number of packet
	[float]	PROB_TH: probability threshold

	[int]	LengthAwkSlpCyl(lambd, DATA_TH, PROB_TH)
	[int]	DataAcc(lambd, K, PROB_TH)
"""
Llambd = 10;
Mlambd = 50;
Hlambd = 250;

SBufSize = {'D': 800};
LBufSize = {'D': 8000};

pktSize = 800;
PROB_TH = 0.8;

if __name__ == '__main__':

	"""
		target: using const lambda to discuss the relation between K and DataAcc
	"""
	testUE= UE(LBufSize, 'D', Llambd);
	DATA_TH= int(testUE.buf[testUE.status] * 0.8 / pktSize);
	print(DATA_TH)
	PROB_TH= 0.8;
	K1= LengthAwkSlpCyl(testUE.lambd, DATA_TH, PROB_TH)
	K2= K1
	K2_DataAcc= DataAcc(testUE.lambd, K2, PROB_TH)
	print(K2)
