import sys
import logging

sys.path.append('../..')
from lbps.tdd.basic import one2all as M1
from lbps.tdd.basic import continuous as M2
from lbps.tdd.basic import one2one_first as M3


class IntegratedTwoHop(object):
    def __init__(self, root, backhaul_timeline, access_timeline):
        self.root = root
        self.__backhaul = backhaul_timeline
        self.__access = access_timeline