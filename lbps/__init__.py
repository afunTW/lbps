# -*- coding: utf-8 -*-
#!/usr/bin/python3

import random
import copy
from device import UE, RN, eNB
from config import *

"""
Capacity
# N_TTI_OFDM: number of OFDM symbol in one TTI
# N_CTRL_OFDM: number of OFDM symbol in one TTI for signaling
# RBG: one TTI conatin two RBs equal to one RBG
# N_TTI_RE: number of RE in one TTI for data transmission

Capacity = total REs * Eff(REs)

Efficiency have to map to T_CQI by wideband or sub-band
"""
N_TTI_OFDM = 14
N_CTRL_OFDM = 2
N_RBG = 100
N_S_RBG = 8

# one TTI, one RBG
N_TTI_RE = (N_TTI_OFDM-N_CTRL_OFDM)*12

# one TTI, total RBGs = total REs
N_TTI_RE = N_TTI_RE*N_RBG

# Capacity of wideband
def wideband_capacity(l_UE):
    """
    input a list of UE with bunch of different CQI,
    wideband will only calc by one avg. CQI
    """
    W_CQI = sum(l_UE.CQI)/len(l_UE);
    return N_TTI_RE*T_CQI[int(W_CQI)]*N_RBG;

# Capacity of sub-band
def subband_capacity(l_UE):
    """
    input a list of UE with bunch of different CQI
    subband have to calc case by case then summation
    """
    return sum(N_TTI_RE*T_CQI[l_UE.CQI]*N_RBG)
