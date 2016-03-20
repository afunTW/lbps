#!/usr/bin/python3

# CQI = { CQI_index: modulation, code_rate*1024, efficiency }
CQI = {
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
        15: { 'modulation': '64QAM', 'code-rate': 948, 'eff': 5.5547 },
    };

# TDD_config = { index: [ DL/Special/UL subframe] }
TDD_config = {
        0: ['D', 'S', 'U', 'U', 'U', 'D', 'S', 'U', 'U', 'U'],
        1: ['D', 'S', 'U', 'U', 'D', 'D', 'S', 'U', 'U', 'D'],
        2: ['D', 'S', 'U', 'D', 'D', 'D', 'S', 'U', 'D', 'D'],
        3: ['D', 'S', 'U', 'U', 'U', 'D', 'D', 'D', 'D', 'D'],
        4: ['D', 'S', 'U', 'U', 'D', 'D', 'D', 'D', 'D', 'D'],
        5: ['D', 'S', 'U', 'D', 'D', 'D', 'D', 'D', 'D', 'D'],
        6: ['D', 'S', 'U', 'U', 'U', 'D', 'S', 'U', 'U', 'D'],
    };
