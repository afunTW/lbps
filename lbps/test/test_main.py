# -*- coding: utf-8 -*-
#!/usr/bin/python3

import __init__
from poisson import Poisson
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
"""
Xlambd = 3
Llambd = 10
Mlambd = 50
Hlambd = 250

XBufSize = 30
SBufSize = 800
LBufSize = 8000

if __name__ == '__main__':

	"""
		target: using const lambda to discuss the relation between K and DataAcc
	"""
	testUE = UE(buf, [0, XBufSize], 'D');
	testUE.process.timeInterval = 100	;

	K1 = testUE.process.LengthAwkSlpCyl(0.8 * testUE.buf[1], 0.8);
	print(list(range(K1)))
