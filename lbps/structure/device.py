import sys
import logging

sys.path.append('../..')
from src import cqi
from src import tdd
from src import bearer
from src import traffic
from src import capacity


class OneHopDevice(object):
    count = 0

    def __init__(self, name=None):
        self.name = (
            name or '_'.join(
                [self.__class__.__name__, str(self.__class__.count)]
            )
        )
        self.buffer = []
        self.sleep = False
        self.__bearer = []
        self.__tdd_config = []
        self.__division_mode = 'TDD'

    @property
    def bearer(self):
        return self.__bearer

    def append_bearer(self, b):
        try:
            assert isinstance(b, bearer.Bearer),\
            'given data is not bearer.Bearer'
            self.__bearer.append(b)
        except Exception as e:
            logging.exception(e)

    def clear_bearer(self):
        self.__bearer = []

    @property
    def target_device(self):
        assert self.__bearer, '%s have no connected to another device' % self.name
        def get_target_device(bearer):
            assert isinstance(bearer, bearer.Bearer)
            if bearer.source is self:
                return bearer.destination
            elif bearer.destination is self:
                return bearer.source
        return [get_target_device(b) for b in self.__bearer]

    @property
    def tdd_config(self):
        return self.__tdd_config

    @tdd_config.setter
    def tdd_config(self, conf):
        try:
            if instance(conf, int):
                assert conf in tdd.one_hop_config.keys(),\
                self.name + ' given index out of range'
                self.__tdd_config = tdd.one_hop_config[conf]
            elif isinstance(conf, list):
                assert all(map(is_tdd_config, conf)),\
                self.name + 'tdd config validation failed'
                assert len(conf) == 10,\
                self.name + ' given list length should be 10'
                self.__tdd_config = conf
            else:
                raise Exception(
                    self.name + ' given tdd config shuold be int either list'
                )
        except Exception as e:
            logging.exception(e)

    @property
    def lambd(self):
        try:
            aggr_lambd = [b.flow.lambd for b in self.__bearer]
            return round(sum(aggr_lambd), 2)
        except Exception as e:
            logging.exception(e)

    @property
    def wideband_capacity(self):
        try:
            assert self.__bearer, self.name + ' no bearer given'
            each_cqi = [bearer.CQI for bearer in self.__bearer]
            each_eff = [cqi.cqi_info(i)['eff'] for i in each_cqi]
            aggr_cap = sum([capacity.RE_TTI*eff for eff in each_eff])
            return aggr_cap
        except Exception as e:
            logging.exception(e)

    @property
    def virtual_capacity(self):
        try:
            assert self.__tdd_config, self.name + ' tdd config is empty'
            avaliable_frame_cap = \
            self.__tdd_config.count('D') * self.wideband_capacity
            return int(avaliable_frame_cap/10)
        except Exception as e:
            logging.exception(e)

    @property
    def lbps_capacity(self):
        if self.division_mode and self.division_mode == 'TDD':
            return self.virtual_capacity
        if self.division_mode and self.division_mode == 'FDD':
            return self.wideband_capacity

    @property
    def division_mode(self):
        return self.__division_mode

    @division_mode.setter
    def division_mode(self, mode):
        try:
            assert isinstance(mode, str), 'given mode is not string'
            assert mode in ['FDD', 'TDD'], 'given mode is not FDD either TDD'
            self.__division_mode = mode
        except Exception as e:
            raise e

    @classmethod
    def is_tdd_config(cls, conf):
        try:
            assert isinstance(conf, str),\
            cls.name + ' tdd config validation with non-string'
            assert len(conf) == 1,\
            cls.name + ' tdd config validation over length'
            return conf in ['D', 'U', '']
        except Exception as e:
            logging.exception(e)


class TwoHopDevice(OneHopDevice):
    count = 0

    def __init__(self, name=None):
        self.name = (
            name or '_'.join(
                [self.__class__.__name__, str(self.__class__.count)]
            )
        )
        self.backhaul = super().__init__(name=name)
        self.access = super().__init__(name=name)
        self.__tdd_config = None
        self.__sleep = False

    @property
    def sleep(self):
        return self.__sleep

    @sleep.setter
    def sleep(self, mode):
        try:
            assert isinstance(mode, bool), \
            self.name + ' mode is not bool'
            self.__sleep = mode
            self.backhaul.sleep = mode
            self.access.slepp = mode
        except Exception as e:
            raise e

    @property
    def tdd_config(self):
        return self.__tdd_config

    @tdd_config.setter
    def tdd_config(self, index):
        assert isinstance(index, int),\
        self.name + ' given index is not int'
        assert index in tdd.two_hop_config.keys(),\
        self.name + ' given index out of range'
        self.__tdd_config = two_hop_config[index]
        self.backhaul.tdd_config = two_hop_config[index]['backhaul']
        self.access.tdd_config = two_hop_config[index]['access']