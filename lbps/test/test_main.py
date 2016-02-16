# -*- coding: utf-8 -*-                                                                                                                       
#!/usr/bin/python3

import __init__
from poisson import Poisson
from device import Device, UE

Xlambd = 3	# bit
Llambd = 10		# kbps
Mlambd = 50		# kbps
Hlambd = 250	# kbps

XBufSize = 30	# bit
SBufSize = 0.8	# kbit
LBufSize = 8		# kbit

if __name__ == '__main__':
	
	"""
		target: using const lambda to discuss the relation between K and DataAcc
	"""
	testUE = UE(Xlambd, [0, XBufSize], 'D');
	testUE.process.timeInterval = 100	;

	K1 = testUE.process.LengthAwkSlpCyl(0.8 * testUE.buf[1], 0.8);
	print(list(range(K1)))
