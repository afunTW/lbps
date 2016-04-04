#!/usr/bin/python3

"""
Capacity
# BANDWIDTH: 0.2 MHz = 12 subcarriers = 1 RBG = 2RBs
# N_TTI_OFDM: number of OFDM symbol in one TTI
# N_CTRL_OFDM: number of OFDM symbol in one TTI for signaling
# RBG: one TTI conatin two RBs equal to one RBG
# N_TTI_RE: number of RE in one TTI for data transmission

Capacity = total REs * Eff(REs)

Efficiency have to map to T_CQI by wideband or sub-band
"""
BANDWIDTH = 20

N_TTI_OFDM = 14
N_CTRL_OFDM = 2
N_RBG = int(BANDWIDTH / 0.2)
N_S_RBG = 8

# one TTI, one RBG
N_TTI_RE = (N_TTI_OFDM - N_CTRL_OFDM) * 12

# one TTI, total RBGs = total REs
N_TTI_RE = N_TTI_RE * N_RBG

def wideband_capacity(device, interface):
	W_CQI = sum(d.link[interface].CQI for d in device) / len(device)
	return N_TTI_RE * T_CQI[int(W_CQI)]['eff'] * N_RBG

"""
# CQI related
"""
T_CQI = {
	1: { 'modulation': 'QPSK', 'code-rate': 78, 'eff': 0.1523 },
	2: { 'modulation': 'QPSK', 'code-rate': 120, 'eff': 0.2344 },
	3: { 'modulation': 'QPSK', 'code-rate': 193, 'eff': 0.3770 },
	4: { 'modulation': 'QPSK', 'code-rate': 308, 'eff': 0.6016 },
	5: { 'modulation': 'QPSK', 'code-rate': 449, 'eff': 0.8770 },
	6: { 'modulation': 'QPSK', 'code-rate': 602, 'eff': 1.1758 },
	7: { 'modulation': '16QAM', 'code-rate': 378, 'eff': 1.4766 },
	8: { 'modulation': '16QAM', 'code-rate': 490, 'eff': 1.9141 },
	9: { 'modulation': '16QAM', 'code-rate': 616, 'eff': 2.4063 },
	10: { 'modulation': '64QAM', 'code-rate': 466, 'eff': 2.7305 },
	11: { 'modulation': '64QAM', 'code-rate': 567, 'eff': 3.3223 },
	12: { 'modulation': '64QAM', 'code-rate': 666, 'eff': 3.9023 },
	13: { 'modulation': '64QAM', 'code-rate': 772, 'eff': 4.5234 },
	14: { 'modulation': '64QAM', 'code-rate': 873, 'eff': 5.1152 },
	15: { 'modulation': '64QAM', 'code-rate': 948, 'eff': 5.5547 }
};

# CQI type for device setting
DEVICE_CQI_TYPE = {
	'L': [1, 2, 3, 4, 5, 6],
	'M': [7, 8, 9],
	'H': [10, 11, 12, 13, 14, 15]
}

"""
TDD configuration
"""

ONE_HOP_TDD_CONFIG = {
	0: ['D', 'S', 'U', 'U', 'U', 'D', 'S', 'U', 'U', 'U'],
	1: ['D', 'S', 'U', 'U', 'D', 'D', 'S', 'U', 'U', 'D'],
	2: ['D', 'S', 'U', 'D', 'D', 'D', 'S', 'U', 'D', 'D'],
	3: ['D', 'S', 'U', 'U', 'U', 'D', 'D', 'D', 'D', 'D'],
	4: ['D', 'S', 'U', 'U', 'D', 'D', 'D', 'D', 'D', 'D'],
	5: ['D', 'S', 'U', 'D', 'D', 'D', 'D', 'D', 'D', 'D'],
	6: ['D', 'S', 'U', 'U', 'U', 'D', 'S', 'U', 'U', 'D']
};

TWO_HOP_TDD_CONFIG = {
		0:[None, None, None, None, 'D', None, None, None, 'U', None],
		1:[None, None, None, 'U', None, None, None, None, None, 'D'],
		2:[None, None, None, None, 'D', None, None, None, 'U', 'D'],
		3:[None, None, None, 'U', 'D', None, None, None, None, 'D'],
		4:[None, None, None, 'U', 'D', None, None, None, 'U', 'D'],
		5:[None, None, 'U', None, None, None, None, None, 'D', None],
		6:[None, None, None, 'D', None, None, None, 'U', None, None],
		7:[None, None, 'U', None, 'D', None, None, None, 'D', None],
		8:[None, None, None, 'D', None, None, None, 'U', None, 'D'],
		9:[None, None, 'U', 'D', 'D', None, None, None, 'D', None],
		10:[None, None, None, 'D', None, None, None, 'U', 'D', 'D'],
		11:[None, None, None, 'U', None, None, None, 'D', None, 'D'],
		12:[None, None, None, 'U', None, None, None, 'D', 'D', 'D'],
		13:[None, None, None, 'U', None, None, None, None, None, 'D'],
		14:[None, None, None, 'U', None, None, None, 'D', None, 'D'],
		15:[None, None, None, 'U', None, None, None, None, 'D', 'D'],
		16:[None, None, None, 'U', None, None, None, 'D', 'D', 'D'],
		17:[None, None, None, 'U', 'D', None, None, 'D', 'D', 'D'],
		18:[None, None, None, None, 'U', None, None, None, None, 'D']
};

"""
Packets
# bitrate(Kbps)
# pkt_size(bits)
# delay_budget(ms)
"""
traffic = {
	'VoIP':{
		'bitrate': 10,
		'pkt_size': 800,
		'delay_budget': 50
	},
	'Video':{
		'bitrate': 250,
		'pkt_size': 8000,
		'delay_budget': 300
	},
	'OnlineVideo':{
		'bitrate': 10,
		'pkt_size': 800,
		'delay_budget': 300
	}
}

"""
Device config
BUF = {'D': [bits], 'U': [bits]}
"""
M_BUF = {'D': 8000, 'U': 8000}
H_BUF = {'D': 80000, 'U': 80000}