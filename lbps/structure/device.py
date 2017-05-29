import sys

sys.path.append('../..')
from src import cqi
from src import tdd
from src import bearer
from src import traffic
from src import capacity


class OneHopDevice(object):

    def __init__(self, name=None, ref_backhaul=None, ref_access=None):
        self.name = name or self.__class__.__name__
        self.buffer = []
        self.sleep = False
        self.ref_backhaul = ref_backhaul
        self.ref_access = ref_access
        self.__bearer = []
        self.__tdd_config = []
        self.__division_mode = 'TDD'

    @property
    def bearer(self):
        return self.__bearer

    def append_bearer(self, b):
        assert isinstance(b, bearer.Bearer),\
        'given data is not bearer.Bearer'
        self.__bearer.append(b)

    def clear_bearer(self):
        self.__bearer = []

    @property
    def target_device(self):
        assert self.__bearer, '%s have no connected to another device' % self.name
        return list(set([self.get_target_device(b) for b in self.__bearer]))

    @property
    def tdd_config(self):
        return self.__tdd_config

    @tdd_config.setter
    def tdd_config(self, conf):
        assert (
            conf in tdd.one_hop_config.values() or
            conf in [_['backhaul'] for _ in tdd.two_hop_config.values()]
        )
        self.__tdd_config = conf

    @property
    def lambd(self):
        aggr_lambd = [b.flow.lambd for b in self.__bearer]
        return round(sum(aggr_lambd), 2)

    @property
    def wideband_capacity(self):
        assert self.__bearer, self.name + ' no bearer given'
        each_cqi = [bearer.CQI for bearer in self.__bearer]
        each_eff = [cqi.cqi_info[i]['eff'] for i in each_cqi]
        aggr_cap = sum([capacity.RE_TTI*eff for eff in each_eff])
        return int(aggr_cap/len(self.__bearer))

    @property
    def virtual_capacity(self):
        assert self.__tdd_config, self.name + ' tdd config is empty'
        if self.ref_backhaul:
            backhaul_utilization = self.ref_backhaul.load
            backhaul_avaliable_subframe = self.ref_backhaul.tdd_config.count('D')
            access_avaliable_subframe = (
                self.__tdd_config.count('D') -
                backhaul_avaliable_subframe*backhaul_utilization
            )
            avaliable_frame_cap = access_avaliable_subframe*self.wideband_capacity
            return int(avaliable_frame_cap/10)
        else:
            avaliable_frame_cap = \
            self.__tdd_config.count('D') * self.wideband_capacity
            return int(avaliable_frame_cap/10)

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
        assert isinstance(mode, str), 'given mode is not string'
        assert mode in ['FDD', 'TDD'], 'given mode is not FDD either TDD'
        self.__division_mode = mode

    @property
    def packet_size(self):
        total_pkt_size = sum([b.flow.packet_size for b in self.bearer])
        return total_pkt_size/len(self.bearer)

    @property
    def load(self):
        return self.lambd*self.packet_size/self.wideband_capacity

    @classmethod
    def is_tdd_config(cls, conf):
        assert isinstance(conf, str),\
        cls.name + ' tdd config validation with non-string'
        assert len(conf) == 1,\
        cls.name + ' tdd config validation over length'
        return conf in ['D', 'U', '']

    def get_target_device(self, b):
        assert isinstance(b, bearer.Bearer)
        if b.source is self or isinstance(b.source, TwoHopDevice):
            return b.destination
        elif b.destination is self or isinstance(b.source, TwoHopDevice):
            return b.source


class TwoHopDevice(object):

    def __init__(self, name=None):
        self.name = name or self.__class__.__name__
        self.backhaul = OneHopDevice(name=name)
        self.access = OneHopDevice(name=name)
        self.__tdd_config = None
        self.__sleep = False

    @property
    def sleep(self):
        return self.__sleep

    @sleep.setter
    def sleep(self, mode):
        assert isinstance(mode, bool), (
            self.name + ' mode is not bool'
            )
        self.__sleep = mode
        self.backhaul.sleep = mode
        self.access.slepp = mode

    @property
    def tdd_config(self):
        return self.__tdd_config

    @tdd_config.setter
    def tdd_config(self, index):
        assert isinstance(index, int), (
            self.name + ' given index is not int'
            )
        assert index in tdd.two_hop_config.keys(), (
            self.name + ' given index out of range'
            )
        self.__tdd_config = two_hop_config[index]
        self.backhaul.tdd_config = two_hop_config[index]['backhaul']
        self.access.tdd_config = two_hop_config[index]['access']