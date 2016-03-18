# -*- coding: utf-8 -*-
#!/usr/bin/python3

import __init__
from poisson import LengthAwkSlpCyl, DataAcc
from viewer import *
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

SBufSize = {'D': 800, 'U': 800};
LBufSize = {'D': 8000, 'U': 800};

pktSize = 800;	# bits

if __name__ == '__main__':

	"""
		target: using const lambda to discuss the relation between K and DataAcc
	"""
	testUE= UE(LBufSize, 'D', Mlambd);	# buffer can store 10 pkt, need 16 TTI to transmit 1 pkt
	DATA_TH= int(testUE.buf[testUE.status] * 0.8 / pktSize);
	PROB_TH = 0.8;

	print("#	init");
	print(">	lambd means arrival rate: %g(bit/ ms), needs %d TTI to transmit 1 packet" % (testUE.lambd, pktSize/testUE.lambd));
	print(">	DATA_TH is accumulate %d packet by buffer size %d packet\n" % (DATA_TH, testUE.buf[testUE.status]/pktSize));

	d_K1= LengthAwkSlpCyl(testUE.lambd/pktSize , DATA_TH, PROB_TH, view= True);
	print(">	Get the K1= %d" % sorted(d_K1.keys())[-1]);

	K2= sorted(d_K1.keys())[-1];
	d_K2= DataAcc(testUE.lambd/pktSize, K2, PROB_TH, view= True);
	print(">	Accumulate Data in %d TTI: %d packet" % (K2, sorted(d_K2.keys())[-1]));

	d_K3= LengthAwkSlpCyl(testUE.lambd/pktSize , DATA_TH, 1- PROB_TH, view= True);
	print(">	Get the K1= %d" % sorted(d_K3.keys())[-1]);

	K4= sorted(d_K3.keys())[-1];
	d_K4= DataAcc(testUE.lambd/pktSize, K4, PROB_TH, view= True);
	print(">	Accumulate Data in %d TTI: %d packet" % (K4, sorted(d_K4.keys())[-1]));

	"""
		Plotting the result
	"""
	plt.figure(1);
	plt.title("Calculating sleep cycle length/ data accumulation");

	plt.subplot(221);
	# plt.title("Data_TH= %d, Prob_TH= %g %%"% (DATA_TH, PROB_TH*100))
	plt.xlabel("K(TTI)");
	plt.ylabel("P");
	plt.text(0.05*sorted(d_K1.keys())[-1], 0.8*sorted(d_K1.values())[-1],
			"K1= %d\nDATA_TH= %d packet\nPROB_TH= %g %%"% (sorted(d_K1.keys())[-1], DATA_TH, PROB_TH*100),
			fontsize= 12, bbox= {'facecolor': 'yellow', 'alpha': 0.5})
	plt.plot(sorted(d_K1.keys()), sorted(d_K1.values()), color= 'red');
	plt.grid(True);

	plt.subplot(223);
	plt.xlabel("#pkt");
	plt.ylabel("P");
	plt.text(0.5, 0.6,
			"K2= %d\nDATA_TH= %d packet\nPROB_TH= %g %%"% (sorted(d_K1.keys())[-1], sorted(d_K2.keys())[-1], PROB_TH*100),
			fontsize= 12, bbox= {'facecolor': 'yellow', 'alpha': 0.5})
	plt.plot(sorted(d_K2.keys()), sorted(d_K2.values()), color= 'red');
	plt.grid(True);

	plt.subplot(222);
	plt.title("Data_TH= %d, Prob_TH= %g %%"% (DATA_TH, (1-PROB_TH)*100))
	plt.xlabel("K(TTI)");
	plt.ylabel("P");
	plt.text(0.05*sorted(d_K3.keys())[-1], 0.8*sorted(d_K3.values())[-1],
			"K1= %d\nDATA_TH= %d packet\nPROB_TH= %g %%"% (sorted(d_K3.keys())[-1], DATA_TH, (1-PROB_TH)*100),
			fontsize= 12, bbox= {'facecolor': 'yellow', 'alpha': 0.5})
	plt.plot(sorted(d_K3.keys()), sorted(d_K3.values()), color= 'blue');
	plt.grid(True);

	plt.subplot(224);
	plt.xlabel("#pkt");
	plt.ylabel("P");
	plt.text(0.5, 0.6,
			"K2= %d\nDATA_TH= %d packet\nPROB_TH= %g %%"% (sorted(d_K3.keys())[-1], sorted(d_K4.keys())[-1], PROB_TH*100),
			fontsize= 12, bbox= {'facecolor': 'yellow', 'alpha': 0.5})
	plt.plot(sorted(d_K4.keys()), sorted(d_K4.values()), color= 'blue');
	plt.grid(True);

	plt.show();
