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
import logging
import traceback

BANDWIDTH = 20
N_TTI_OFDM = 14
N_CTRL_OFDM = 2
N_RBG = int(BANDWIDTH / 0.2)
N_S_RBG = 8