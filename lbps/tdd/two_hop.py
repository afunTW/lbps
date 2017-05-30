import sys
import lbps
import logging

sys.path.append('../..')
from lbps.tdd.basic import one2all as M1
from lbps.tdd.basic import continuous as M2
from lbps.tdd.basic import one2one_first as M3
from math import ceil


class IntegratedTwoHop(object):
    def __init__(self, root, backhaul_timeline, access_timeline, access_only):
        assert access_only in [lbps.MAPPING_M2, lbps.MAPPING_M3]

        self.ID_ACCESS = 0
        self.ID_MIXED = 1
        self.root = root
        self.__b_timeline = backhaul_timeline
        self.__a_timeline = access_timeline
        self.__access_only_mapping = access_only

        self.__check()
        self.__b_tdd_config = self.root.tdd_config
        self.__a_tdd_config = self.root.target_device[0].access.tdd_config

    def __check(self):
        access_tdd_config = [
            str(rn.access.tdd_config) for rn in self.root.target_device
        ]
        access_tdd_config = list(set(access_tdd_config))
        assert len(access_tdd_config) == 1

    def __map_by_pattern(self, pattern, v_timeline):

        # timeline alignment
        extend = lambda x: x*ceil(self.root.simulation_time/len(x))
        alignment = lambda x: extend(x)[:self.root.simulation_time]
        v_timeline = alignment(v_timeline)
        pattern = alignment(pattern)
        actual_timeline = [[] for _ in range(self.root.simulation_time)]

        # map
        for slot in range(0, self.root.simulation_time, 10):
            for TTI in range(slot, slot+10):
                assert TTI < len(v_timeline) and TTI < len(pattern)
                if v_timeline[TTI]:
                    for target_TTI in pattern[TTI]:
                        actual_timeline[slot+target_TTI] += v_timeline[TTI]

        return actual_timeline

    def __map_by_capacity(self, virtual_obj, actual_obj):
        virtual_obj['r_TTI'].append(actual_obj['r_TTI'])
        if virtual_obj['vsc'] >= actual_obj['rsc']:
            virtual_obj['vsc'] -= actual_obj['rsc']
            actual_obj['rsc'] = 0
        else:
            actual_obj['rsc'] -= virtual_obj['vsc']
            virtual_obj['vsc'] = 0

    def __access_pattern(self, backhaul_pattern, backhaul_load):
        flatten = lambda x: [ j for i in x for j in i]
        average = lambda x: sum(x)/len(self.root.target_device)
        non_access_utilization = 1 - backhaul_load
        non_access_index = list(set(flatten(backhaul_pattern)))
        rsc = average([rn.access.wideband_capacity for rn in self.root.target_device])
        vsc = average([rn.access.lbps_capacity for rn in self.root.target_device])

        actual_timeline = [{
            'r_TTI': i,
            'rsc': rsc * (non_access_utilization if i in non_access_index else 1),
            'id': self.ID_MIXED if i in non_access_index else self.ID_ACCESS
        } for i in range(10) if self.__a_tdd_config[i] is 'D']

        virtual_timeline = [{
            'r_TTI': [], 'vsc': vsc
        } for i in range(10)]

        logging.debug('total rsc={} total vsc={}'.format(
            sum([i['rsc'] for i in actual_timeline]),
            sum([i['vsc'] for i in virtual_timeline])
            ))

        # map non-access-only first
        for rk, rv in enumerate(actual_timeline):
            if rv['id'] == self.ID_MIXED:
                low_priority = {}

                # one-to-one first
                for ref, ref_v in enumerate(backhaul_pattern):
                    if not rv['rsc']: break
                    if rv['r_TTI'] in ref_v:
                        if len(ref_v) > 1:
                            low_priority[ref] = ref_v
                            continue
                        self.__map_by_capacity(virtual_timeline[ref], rv)

                # one-to-n
                if rv['rsc']:
                    for ref, ref_v in low_priority:
                        if not rv['rsc']: break
                        self.__map_by_capacity(virtual_timeline[ref], rv)
                assert not rv['rsc']

        # map access-only
        if self.__access_only_mapping == lbps.MAPPING_M2:
            for rk, rv in enumerate(actual_timeline):
                for vk, vv in enumerate(virtual_timeline):
                    if not rv['rsc']: break
                    if not vv['vsc']: continue
                    self.__map_by_capacity(vv, rv)
        elif self.__access_only_mapping == lbps.MAPPING_M3:
            # one-to-one
            for rk, rv in enumerate(actual_timeline):
                for vk, vv in enumerate(virtual_timeline):
                    if not vv['r_TTI'] and rv['rsc'] >= vv['vsc']:
                        self.__map_by_capacity(vv, rv)
            # one-to-n
            for rk, rv in enumerate(actual_timeline):
                for vk, vv in enumerate(virtual_timeline):
                    if not rv['rsc']: break
                    if not vv['vsc']: continue
                    self.__map_by_capacity(vv, rv)

        return [TTI['r_TTI'] for TTI in virtual_timeline]

    def mapping(self):
        '''
        input backhaul and access virtual timeline
        output mappin actual timeline
        '''
        extend = lambda x: x*ceil(self.root.simulation_time/len(x))
        alignment = lambda x: extend(x)[:self.root.simulation_time]

        # backhaul M2 mapping
        backhaul_mapping = M2(self.__b_tdd_config)
        backhaul_pattern = backhaul_mapping.pattern
        access_pattern = self.__access_pattern(backhaul_pattern, self.root.load)
        logging.debug('backhaul mapping pattern {}'.format(backhaul_pattern))
        logging.debug('access mapping pattern {}'.format(access_pattern))

        actual_backhaul_timeline = self.__map_by_pattern(
            backhaul_pattern, self.__b_timeline)
        actual_access_timeline = self.__map_by_pattern(
            access_pattern, self.__a_timeline)

        return actual_backhaul_timeline, actual_access_timeline
