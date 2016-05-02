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
# N_RBG = int(BANDWIDTH / 0.2)
N_S_RBG = 8

# one TTI, one RBG
N_TTI_RE = (N_TTI_OFDM - N_CTRL_OFDM) * 12

# # one TTI, total RBGs = total REs
# N_TTI_RE = N_TTI_RE * N_RBG

def wideband_capacity(device, interface):

	try:
		link_count = len(device.link[interface])
		RB = [ device.link[interface][i].bandwidth for i in range(link_count)]
		RE = [ N_TTI_RE * RB[i] for i in range(link_count)]

		if link_count is 0:
			return None

		return sum(RE[i] * T_CQI[device.link[interface][i].CQI]['eff'] for i in range(link_count)) / link_count

	except Exception as e:
		print("W-capacity\t\t%s"%e)

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
		0: {'backhaul': [None, None, None, None, 'D', None, None, None, 'U', None],
			'access': ONE_HOP_TDD_CONFIG[1]},
		1: {'backhaul': [None, None, None, 'U', None, None, None, None, None, 'D'],
			'access': ONE_HOP_TDD_CONFIG[1]},
		2: {'backhaul': [None, None, None, None, 'D', None, None, None, 'U', 'D'],
			'access': ONE_HOP_TDD_CONFIG[1]},
		3: {'backhaul': [None, None, None, 'U', 'D', None, None, None, None, 'D'],
			'access': ONE_HOP_TDD_CONFIG[1]},
		4: {'backhaul': [None, None, None, 'U', 'D', None, None, None, 'U', 'D'],
			'access': ONE_HOP_TDD_CONFIG[1]},
		5: {'backhaul': [None, None, 'U', None, None, None, None, None, 'D', None],
			'access': ONE_HOP_TDD_CONFIG[2]},
		6: {'backhaul': [None, None, None, 'D', None, None, None, 'U', None, None],
			'access': ONE_HOP_TDD_CONFIG[2]},
		7: {'backhaul': [None, None, 'U', None, 'D', None, None, None, 'D', None],
			'access': ONE_HOP_TDD_CONFIG[2]},
		8: {'backhaul': [None, None, None, 'D', None, None, None, 'U', None, 'D'],
			'access': ONE_HOP_TDD_CONFIG[2]},
		9: {'backhaul': [None, None, 'U', 'D', 'D', None, None, None, 'D', None],
			'access': ONE_HOP_TDD_CONFIG[2]},
		10: {'backhaul': [None, None, None, 'D', None, None, None, 'U', 'D', 'D'],
			'access': ONE_HOP_TDD_CONFIG[2]},
		11: {'backhaul': [None, None, None, 'U', None, None, None, 'D', None, 'D'],
			'access': ONE_HOP_TDD_CONFIG[3]},
		12: {'backhaul': [None, None, None, 'U', None, None, None, 'D', 'D', 'D'],
			'access': ONE_HOP_TDD_CONFIG[3]},
		13: {'backhaul': [None, None, None, 'U', None, None, None, None, None, 'D'],
			'access': ONE_HOP_TDD_CONFIG[4]},
		14: {'backhaul': [None, None, None, 'U', None, None, None, 'D', None, 'D'],
			'access': ONE_HOP_TDD_CONFIG[4]},
		15: {'backhaul': [None, None, None, 'U', None, None, None, None, 'D', 'D'],
			'access': ONE_HOP_TDD_CONFIG[4]},
		16: {'backhaul': [None, None, None, 'U', None, None, None, 'D', 'D', 'D'],
			'access': ONE_HOP_TDD_CONFIG[4]},
		17: {'backhaul': [None, None, None, 'U', 'D', None, None, 'D', 'D', 'D'],
			'access': ONE_HOP_TDD_CONFIG[4]},
		18: {'backhaul': [None, None, None, None, 'U', None, None, None, None, 'D'],
			'access': ONE_HOP_TDD_CONFIG[5]}
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

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

MODE = "DEBUG"
# MODE = "RELEASE"