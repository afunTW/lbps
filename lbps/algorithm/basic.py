import sys
import random
import logging

sys.path.append('../..')
from lbps.structure import device
from lbps.algorithm import poisson


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
