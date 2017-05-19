import sys
import random
import logging

sys.path.append('../..')
from lbps.structure import device
from lbps.algorithm import poisson
from math import log
from math import ceil
from math import floor


class BaseLBPS(object):
    def __init__(self, root, threshold_percentage=0.8):
        assert (
            isinstance(root, device.OneHopDevice) or
            isinstance(root, device.TwoHopDevice)
            ), 'given root is not fit in lbps structure'

        if isinstance(root, device.TwoHopDevice):
            root = root.access

        self.threshold_percentage=threshold_percentage
        self.__root = root

    @property
    def root(self):
        return self.__root

    @property
    def capacity(self):
        return self.root.lbps_capacity

    @property
    def packet_size(self):
        total_pkt_size = sum([b.flow.packet_size for b in self.root.bearer])
        return total_pkt_size/len(self.root.bearer)

    @property
    def load(self):
        return self.root.lambd*self.packet_size/self.root.lbps_capacity

    @property
    def data_threshold(self):
        return self.capacity/self.packet_size*self.threshold_percentage

    def sleep_cycle(self, lambd=None, data_threshold=None):
        if not lambd: lambd = self.root.lambd
        if not data_threshold: data_threshold = self.data_threshold
        K = poisson.get_sleep_cycle(lambd, data_threshold)
        logging.debug(' - sleep cycle {}'.format(K))
        return K


class Aggr(BaseLBPS):
    def __init__(self, root):
        super().__init__(root)

    def run(self):
        logging.info('{} running aggr'.format(self.root.name))
        logging.info(' - load {}'.format(self.load))
        sleep_cycle = self.sleep_cycle()

        timeline = [[] for i in range(sleep_cycle)]
        timeline[0] = [i for i in self.root.target_device]
        timeline[0].append(self.root)
        return timeline


class Split(BaseLBPS):
    def __init__(self, root):
        super().__init__(root)
        self.__groups = {}

    @property
    def groups(self):
        return self.__groups

    def run(self, boundary=None):
        logging.info('{} running split'.format(self.root.name))
        logging.info(' - load {}'.format(self.load))
        sleep_cycle = self.sleep_cycle()

        if boundary:
            assert isinstance(boundary, int)

        if not boundary or boundary > len(self.root.target_device):
            boundary = len(self.root.target_device)


        while True:
            groups = { i: {
                'device': [], 'lambda': 0, 'K': 0
            } for i in range(min(sleep_cycle, boundary))}

            for i in self.root.target_device:

                # find minumn lambda group
                min_lambd = min([groups[g]['lambda'] for g in groups])
                target = [g for g in groups if groups[g]['lambda'] == min_lambd]
                target = random.choice(target)

                # append device to minimum lambda group
                groups[target]['device'].append(i)
                groups[target]['lambda'] += i.lambd
                groups[target]['K'] = self.sleep_cycle(groups[target]['lambda'])

            K = min(groups[g]['K'] for g in groups)
            logging.info(' - iteration with sleep cycle {}'.format(K))

            if K == sleep_cycle: break
            elif len(groups) == boundary:
                sleep_cycle = K if K > 0 else sleep_cycle
                break
            else:
                sleep_cycle = K if K > 0 else sleep_cycle

        self.__groups = groups
        timeline = [[] for i in range(sleep_cycle)]

        for i in groups:
            groups[i]['device'] and groups[i]['device'].append(self.root)
            timeline[i] += groups[i]['device']

        return timeline


class Merge(BaseLBPS):
    def __init__(self, root):
        super().__init__(root)
        self.__groups = {}
        self.__non_degraded_status = False

    @property
    def groups(self):
        return self.__groups

    def schedulability(self, sleep_cycle):
        assert isinstance(sleep_cycle, list)
        assert all(map(lambda x: isinstance(x, int), sleep_cycle))
        result = sum([1/K for K in sleep_cycle]) <= 1
        logging.debug(' - check schedulability: {}'.format(result))
        return result

    def non_degraded_merge(self, groups):
        assert isinstance(groups, list)
        assert all(map(lambda x: isinstance(x, dict), groups))

        if len(groups) == 1:
            logging.debug(' - non degraded merge, nothing changed')
            return groups

        groups.sort(key=lambda x: x['K'], reverse=True)
        src_g = groups.pop(0)
        self.__non_degraded_status = False

        for g in groups:
            new_K = self.sleep_cycle(src_g['lambda'] + g['lambda'])
            new_K = 2**(floor(log(new_K, 2)))

            if new_K == g['K']:
                g['device'] += src_g['device']
                g['lambda'] += src_g['lambda']
                self.__non_degraded_status = True
                logging.debug(' - non degraded merge, success')
                break

        not self.__non_degraded_status and groups.append(src_g)
        groups.sort(key=lambda x: x['K'], reverse=True)
        return groups

    def run(self):
        logging.info('{} running merge'.format(self.root.name))
        logging.info(' - load {}'.format(self.load))
        sleep_cycle = self.sleep_cycle()

        groups = [{
            'device': [i],
            'lambda': i.lambd,
            'K': 2**floor(log(sleep_cycle, 2))
        } for i in self.root.target_device]

        while True:
            if self.schedulability([g['K'] for g in groups]): break

            # non degradeed merge
            groups = self.non_degraded_merge(groups)

            # degraded merge if non-degraded merge failed
            if not self.__non_degraded_status and len(groups) > 1:
                groups[1]['device'] += groups[0]['device']
                groups[1]['lambda'] += groups[0]['lambda']
                groups[1]['K'] = self.sleep_cycle(groups[1]['lambda'])
                groups.pop(0)
                logging.debug(' - non degraded merge, failed')
                logging.debug(' - degraded merge, done')

        # schedule groups
        max_K = max([g['K'] for g in groups])
        groups.sort(key=lambda x: x['K'])
        timeline = [[] for i in range(max_K)]

        for i, g in enumerate(groups):
            base = next((TTI for TTI, _ in enumerate(timeline) if not _), None)
            assert base is not None

            for TTI in range(base, max_K, g['K']):
                timeline[TTI] = g['device'] + [self.root]

        return timeline
