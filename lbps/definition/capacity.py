"""
Capacity
# BANDWIDTH: 0.2 MHz = 12 subcarriers = 1 RBG = 2RBs
# OFDM_TTI: number of OFDM symbol in one TTI
# OFDM_CTRL_TTI: number of OFDM symbol in one TTI for signaling
# RBG: one TTI conatin two RBs equal to one RBG
# RE_TTI: number of RE in one TTI for data transmission

Capacity = total REs * Eff(REs)

Efficiency have to map to T_CQI by wideband or sub-band
"""
import logging
import traceback

BANDWIDTH = 20
OFDM_TTI = 14
OFDM_CTRL_TTI = 2
RBG = int(BANDWIDTH / 0.2)
N_S_RBG = 8
RE_RBG = (OFDM_TTI - OFDM_CTRL_TTI) * 12
RE_TTI = RE_RBG * RBG