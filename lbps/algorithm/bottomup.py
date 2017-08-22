import sys
import logging

sys.path.append('../..')
from math import ceil
from lbps.__init__ import *
from lbps.algorithm import basic
from lbps.algorithm import poisson


class BottomUp(basic.BaseLBPS):
    '''
    Two hop lbps algorithm
    Defined some support function by data structure rn_info:

    backhaul awake: #awake_times for rn in backhaul
    access awake: #awake_times for rn in access for passing data from backhaul
    access K: access sleep cycle for each rn
    schedulability: schedulability for rn in access
    '''
    def __init__(self, root):
        super().__init__(root)
        self.__rn_info = None

    def rn_access_info(self, method):
        assert method in [
            ALGORITHM_LBPS_AGGR, ALGORITHM_LBPS_SPLIT, ALGORITHM_LBPS_MERGE]

        all_rn = self.root.target_device
        self.__rn_info = None

        if method == ALGORITHM_LBPS_AGGR:
            self.__rn_info = { rn: {
            'access_timeline': basic.Aggr(rn.access).run()} for rn in all_rn}
        elif method == ALGORITHM_LBPS_SPLIT:
            self.__rn_info = { rn: {
            'access_timeline': basic.Split(rn.access).run()} for rn in all_rn}
        elif method == ALGORITHM_LBPS_MERGE:
            self.__rn_info = { rn: {
            'access_timeline': basic.Merge(rn.access).run()} for rn in all_rn}

        self.update_rn_access_info()
        return self.__rn_info

    def update_rn_access_info(self):
        for rn, v in self.__rn_info.items():
            rate = rn.access.lbps_capacity / self.root.lbps_capacity
            v['access_K'] = len(v['access_timeline'])
            v['access_awake'] = sum([1 for i in v['access_timeline'] if i])
            v['backhaul_awake'] = ceil(v['access_awake']*rate)

            for i, slot in enumerate(v['access_timeline']):
                self.device_replacement(slot, rn)

    def device_replacement(self, devices, target):
        for i, device in enumerate(devices):
            if device.name == target.name:
                devices[i] = target

    def all_awake(self):
        logging.info(' - schedule failed, all awaken')
        all_rn = [rn for rn in self.root.target_device]
        backhaul_timeline = all_rn + [self.root]
        access_timeline = [
            ue for rn in self.root.target_device for ue in rn.access.target_device]
        access_timeline += all_rn
        return ([backhaul_timeline], [access_timeline])


class MinCycle(BottomUp):
    def __init__(self, root, method):
        super().__init__(root)
        self.__rn_info = self.rn_access_info(method)

    @property
    def rn_info(self):
        return self.__rn_info

    def degrade_cycle(self, rn_info, bound_K):
        for i, rn in enumerate(rn_info):
            if rn_info[rn]['access_K'] > bound_K:
                rn_access_info = basic.BaseLBPS(rn.access)
                packet_size = rn_access_info.packet_size
                accumulate_packet = poisson.get_data_accumulation(
                    rn.access.lambd, bound_K)

                rn_info[rn]['access_K'] = bound_K
                if accumulate_packet:
                    rn_info[rn]['backhaul_awake'] = ceil(
                        accumulate_packet * packet_size / self.root.lbps_capacity)
        return rn_info

    def schedulability(self, bound_K):
        rn_info = self.__rn_info
        checked = lambda x: (x['access_awake']+x['backhaul_awake']) <= bound_K
        backhaul_schedulability = sum([v['backhaul_awake'] for v in rn_info.values()])
        backhaul_schedulability = (backhaul_schedulability <= bound_K)
        access_schedulability = all([checked(v) for v in rn_info.values()])
        return (backhaul_schedulability, access_schedulability)

    def scheduling(self, backhaul_K):
        backhaul_timeline = [[] for TTI in range(backhaul_K)]
        access_timeline = backhaul_timeline.copy()

        for rn, info in self.__rn_info.items():
            for i, slot in enumerate(backhaul_timeline):
                if slot: continue
                for count in range(i, i+info['backhaul_awake']):
                    if count >= len(backhaul_timeline):
                        print(len(backhaul_timeline), i, info['backhaul_awake'], count)
                        break
                    backhaul_timeline[count] += [self.root, rn]
                break
            for i, slot in enumerate(info['access_timeline']):
                if not slot: continue
                access_timeline[i] += slot

        return (backhaul_timeline, access_timeline)


class MinCycleAggr(MinCycle):
    def __init__(self, root):
        super().__init__(root, ALGORITHM_LBPS_AGGR)
        self.__rn_info = self.rn_info

    def run(self):
        backhaul_K = min([v['access_K'] for v in self.__rn_info.values()])
        self.__rn_info = self.degrade_cycle(self.__rn_info, backhaul_K)
        can_backhaul, can_access = self.schedulability(backhaul_K)

        if can_backhaul and can_access:
            return self.scheduling(backhaul_K)
        else:
            return self.all_awake()


class MinCycleSplit(MinCycle):
    def __init__(self, root):
        super().__init__(root, ALGORITHM_LBPS_SPLIT)
        self.__rn_info = self.rn_info

    def run(self):
        backhaul_K = min([v['access_K'] for v in self.__rn_info.values()])
        self.__rn_info = self.degrade_cycle(self.__rn_info, backhaul_K)
        backhaul_timeline = [[] for TTI in range(backhaul_K)]
        access_timeline = backhaul_timeline.copy()

        while True:
            can_backhaul, can_access = self.schedulability(backhaul_K)
            if can_backhaul and can_access:
                return self.scheduling(backhaul_K)
            else:
                logging.debug(' - reversing split')
                reverse_target = None
                for rn, info in self.__rn_info.items():
                    if info['access_K'] == backhaul_K and info['access_awake'] > 1:
                        reverse_target = rn
                        break

                if not reverse_target:
                    return self.all_awake()

                # reversing split and update
                groups = self.__rn_info[reverse_target]['access_awake']
                split_process = basic.Split(rn.access)
                self.__rn_info[reverse_target].update({
                    'access_timeline': split_process.run(boundary=groups-1)
                    })
                self.update_rn_access_info()
                backhaul_K = min([v['access_K'] for v in self.__rn_info.values()])
                self.__rn_info = self.degrade_cycle(self.__rn_info, backhaul_K)


class MergeCycle(BottomUp):
    def __init__(self, root, method):
        super().__init__(root)
        self.__rn_info = self.rn_access_info(method)

    @property
    def rn_info(self):
        return self.__rn_info

    def schedulability(self, groups):
        ratio = lambda g: ceil(g['backhaul_awake']) / g['access_K']
        access_awake = lambda g: sum(
            [self.__rn_info[rn]['access_awake'] for rn in g['device']])
        access_check = lambda g: (
            access_awake(g) + ceil(g['backhaul_awake']) <= g['access_K'])

        can_access = all([access_check(g) for g in groups])
        can_backhaul = (sum([ratio(g) for g in groups]) <= 1)
        logging.info('Check schedulability: ')
        for g in groups:
            logging.info('access_awake={}, backhaul_awake={}, access_K={}'.format(
                access_awake(g), g['backhaul_awake'], g['access_K']
            ))
        logging.info('Check schedulability: access_check={}'.format(
            [access_check(g) for g in groups]))
        logging.info('Check schedulability: can_access={}, can_backhaul={}'.format(can_access, can_backhaul))
        return (can_backhaul, can_access)

    def scheduling(self, groups):
        backhaul_K = max([v['access_K'] for v in self.__rn_info.values()])
        backhaul_timeline = [[] for i in range(backhaul_K)]
        access_timeline = backhaul_timeline.copy()

        for i, group in enumerate(groups):
            TTI = 0
            while TTI < backhaul_K:
                if backhaul_timeline[TTI]:
                    TTI += 1
                    continue
                for count in range(ceil(group['backhaul_awake'])):
                    backhaul_timeline[TTI+count] += group['device']
                    backhaul_timeline[TTI+count] += [self.root]
                TTI += group['access_K']

            for rn in group['device']:
                for i, slot in enumerate(access_timeline):
                    if i >= len(self.__rn_info[rn]['access_timeline']): break
                    slot += self.__rn_info[rn]['access_timeline'][i]

        return (backhaul_timeline, access_timeline)


class MergeCycleMerge(MergeCycle):
    def __init__(self, root):
        super().__init__(root, ALGORITHM_LBPS_MERGE)
        self.__rn_info = self.rn_info
        self.__is_non_degraded = False

    def non_degraded(self, groups):
        logging.info('{} ready for non degraded'.format(self.non_degraded.__name__))
        self.__is_non_degraded = False
        groups.sort(key=lambda x: x['access_K'], reverse=True)
        logging.info('Groups access_K = {}'.format([g['access_K'] for g in groups]))

        for i, source in enumerate(groups):
            for j, target in enumerate(groups[i+1:]):
                same_K = (target['access_K'] == source['access_K'])
                can_backhaul = target['backhaul_awake']+source['backhaul_awake']
                can_backhaul = (ceil(can_backhaul) < source['access_K'])

                if same_K and can_backhaul:
                    access_awake = lambda rn: sum([
                        1 for i in self.__rn_info[rn]['access_timeline'] if i])
                    target_access = sum([access_awake(rn) for rn in target['device']])
                    source_access = sum([access_awake(rn) for rn in source['device']])
                    if target_access + source_access > source['access_K']: break

                self.__is_non_degraded = True
                source['device'] += target['device']
                source['backhaul_awake'] += target['backhaul_awake']
                groups.remove(target)
                break
            else:
                continue
            break

        logging.info('Groups access_K = {}'.format([g['access_K'] for g in groups]))
        logging.info('{} non degraded {}'.format(self.non_degraded.__name__, self.__is_non_degraded))
        return groups

    def run(self):
        groups = [{
            'device': [rn],
            'access_K': info['access_K'],
            'backhaul_awake': info['backhaul_awake']
        } for rn, info in self.__rn_info.items()]

        # backhaul merge process
        ratio = lambda g: ceil(g['backhaul_awake'] / g['access_K'])
        can_merge = lambda x: sum([ratio(g) for g in x]) > 1

        while can_merge(groups):
            groups = self.non_degraded(groups)
            if not self.__is_non_degraded: break

        can_backhaul, can_access = self.schedulability(groups)

        if can_backhaul and can_access:
            return self.scheduling(groups)
        else:
            return self.all_awake()
