import sys
import logging

sys.path.append('../..')
from src import tdd as config


class BaseMapping(object):
    def __init__(self, tdd_config):

        if isinstance(tdd_config, list):
            assert tdd_config in list(config.one_hop_config.values())
        elif isinstance(tdd_config, dict):
            assert tdd_config in list(config.two_hop_config.values())
        else:
            raise Exception('{} not the proper TDD config'.format(tdd_config))

        self.__tdd_config = tdd_config.copy()
        self.__pattern = None

        # real/virtual subframe capacity
        self.__rsc = 10
        self.__vsc = tdd_config.count('D')*self.__rsc/10
        self.__real_timeline = [self.__rsc for i in range(10)]
        self.__virtual_timeline = [{
            'r_TTI': [], 'vsc': self.__vsc
            } for i in range(10)]

    @property
    def rsc(self):
        return self.__rsc

    @rsc.setter
    def rsc(self, capacity):
        assert isinstance(capacity, (int, float))
        self.__rsc = capacity
        self.vsc = self.__rsc
        self.__real_timeline = [self.__rsc for i in range(10)]

    @property
    def vsc(self):
        return self.__vsc

    @vsc.setter
    def vsc(self, rsc):
        assert isinstance(rsc, (int, float))
        self.__vsc = self.__tdd_config.count('D')*rsc/10
        self.__virtual_timeline = [{
            'r_TTI': [], 'vsc': self.__vsc
        } for i in range(10)]

    @property
    def real_timeline(self):
        return self.__real_timeline

    @property
    def virtual_timeline(self):
        return self.__virtual_timeline
