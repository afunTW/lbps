# -*- coding: utf-8 -*-
#!/usr/bin/python3

import random
import copy
from device import UE, RN, eNB
from config import *

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

# Capacity of wideband


def wideband_capacity(l_UE):
    """
    input a list of UE with bunch of different CQI,
    wideband will only calc by one avg. CQI
    """
    W_CQI = sum(l_UE.link.CQI) / len(l_UE)
    return N_TTI_RE * T_CQI[int(W_CQI)]['eff'] * N_RBG

# # Capacity of sub-band
# def subband_capacity(l_UE):
#     """
#     input a list of UE with bunch of different CQI
#     subband have to calc case by case then summation
#     """
#     return sum(N_TTI_RE*T_CQI[l_UE.link.CQI]['eff']*N_RBG)

"""
Device config
BUF = {'D': [bits], 'U': [bits]}
"""
M_BUF = {'D': 8000, 'U': 8000}
H_BUF = {'D': 80000, 'U': 80000}
