import sys
import logging

sys.path.append('../..')
from src import tdd as config
from math import ceil


class BaseMapping(object):
    '''
    Base Mapping class only handle one hop mapping
    '''
    def __init__(self, tdd_config, rsc=10):

        if isinstance(tdd_config, list):
            one_hop = config.one_hop_config.values()
            two_hop = [
                v['backhaul'] for v in config.two_hop_config.values()
            ]
            assert tdd_config in one_hop or tdd_config in two_hop
        else:
            raise Exception('{} not the proper TDD config'.format(tdd_config))

        self.__tdd_config = tdd_config.copy()

        # real/virtual subframe capacity
        self.__rsc = None
        self.__vsc = None
        self.__real_timeline = None
        self.__virtual_timeline = None
        self.rsc = rsc

    @property
    def rsc(self):
        return self.__rsc

    @rsc.setter
    def rsc(self, capacity):
        assert isinstance(capacity, (int, float))
        self.__rsc = capacity
        self.vsc = self.__rsc
        self.__real_timeline = [{
            'r_TTI': i, 'rsc': self.__rsc
        } for i in range(10) if self.__tdd_config[i] is 'D']

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

    def map_by_pattern(self, pattern, v_timeline, simulation_time):
        extend = lambda x: x*ceil(simulation_time/len(x))
        alignment = lambda x: extend(x)[:simulation_time]
        v_timeline = alignment(v_timeline)
        pattern = alignment(pattern)
        actual_timeline = [[] for _ in range(simulation_time)]

        # map
        for slot in range(0, simulation_time, 10):
            for TTI in range(slot, slot+10):
                assert TTI < len(v_timeline) and TTI < len(pattern)
                if v_timeline[TTI]:
                    for target_TTI in pattern[TTI]:
                        actual_timeline[slot+target_TTI] += v_timeline[TTI]

        return actual_timeline

class one2all(BaseMapping):
    '''
    M1 mapping: one to all mapping
    '''
    def __init__(self, tdd_config):
        super().__init__(tdd_config)
        self.__pattern = None
        self.__run()

    @property
    def pattern(self):
        return self.__pattern

    def __run(self):
        for rk, rv in enumerate(self.real_timeline):
            allocate_rsc = rv['rsc']/10
            for vk, vv in enumerate(self.virtual_timeline):
                if vv['vsc'] >= allocate_rsc:
                    vv['vsc'] -= allocate_rsc
                    rv['rsc'] -= allocate_rsc
                    vv['r_TTI'].append(rv['r_TTI'])
        self.__pattern = [v['r_TTI'] for v in self.virtual_timeline]
        return self.__pattern

    def map_by_pattern(self, v_timeline, simulation_time):
        return super().map_by_pattern(self.__pattern, v_timeline, simulation_time)


class continuous(BaseMapping):
    '''
    M2 mapping: continuous mapping
    '''
    def __init__(self, tdd_config):
        super().__init__(tdd_config)
        self.__pattern = None
        self.__run()

    @property
    def pattern(self):
        return self.__pattern

    def __run(self):
        for rk, rv in enumerate(self.real_timeline):
            for vk, vv in enumerate(self.virtual_timeline):
                if not rv['rsc']: break
                elif not vv['vsc']: continue
                elif rv['rsc'] >= vv['vsc']:
                    rv['rsc'] -= vv['vsc']
                    vv['vsc'] = 0
                    vv['r_TTI'].append(rv['r_TTI'])
                else:
                    vv['vsc'] -= rv['rsc']
                    rv['rsc'] = 0
                    vv['r_TTI'].append(rv['r_TTI'])
        self.__pattern = [v['r_TTI'] for v in self.virtual_timeline]
        return self.__pattern

    def map_by_pattern(self, v_timeline, simulation_time):
        return super().map_by_pattern(self.__pattern, v_timeline, simulation_time)


class one2one_first(BaseMapping):
    '''
    M3 mapping: one to one irst mapping
    '''
    def __init__(self, tdd_config):
        super().__init__(tdd_config)
        self.__pattern = None
        self.__run()

    @property
    def pattern(self):
        return self.__pattern

    def __run(self):
        for vk, vv in enumerate(self.virtual_timeline):
            whole_allocated_rsc = any([
                r['rsc'] > vv['vsc'] for r in self.real_timeline])
            for rk, rv in enumerate(self.real_timeline):
                if not vv['vsc']: break
                elif not rv['rsc']: continue
                elif whole_allocated_rsc:
                    if rv['rsc'] < vv['vsc']: continue
                    else:
                        rv['rsc'] -= vv['vsc']
                        vv['vsc'] = 0
                        vv['r_TTI'].append(rv['r_TTI'])
                else:
                    vv['vsc'] -= rv['rsc']
                    rv['rsc'] = 0
                    vv['r_TTI'].append(rv['r_TTI'])
        self.__pattern = [v['r_TTI'] for v in self.virtual_timeline]
        return self.__pattern

    def map_by_pattern(self, v_timeline, simulation_time):
        return super().map_by_pattern(self.__pattern, v_timeline, simulation_time)
