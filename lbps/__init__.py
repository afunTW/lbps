# -*- coding: utf-8 -*-
#!/usr/bin/python3

import random
import copy
from device import UE, RN
from config import *
from viewer import *
from lbps import aggr, split, merge
from tdd import virtual_subframe_capacity as VSC