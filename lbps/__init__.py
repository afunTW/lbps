# -*- coding: utf-8 -*-
#!/usr/bin/python3

import random
import copy
from device import UE, RN, eNB
from config import *
from viewer import *
from lbps import load_based_power_saving as LBPS
from tdd import virtual_subframe_capacity as VSC
from tdd import one_to_one_first_mapping as M3