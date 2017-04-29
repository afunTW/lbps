import sys
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
        avg_pkt_size = self.packet_size
        return self.root.lambd*avg_pkt_size/self.root.lbps_capacity

    @property
    def data_threshold(self):
        return self.capacity/self.packet_size*self.threshold_percentage

    @property
    def sleep_cycle(self):
         return poisson.get_sleep_cycle(self.root.lambd, self.data_threshold)


class Aggr(BaseLBPS):
    def __init__(self, root):
        super().__init__(root)

    def run(self):
        sleep_cycle = self.sleep_cycle
        logging.info('running aggr under {} load'.format(self.load))
        logging.info('{} sleep cycle: {}'.format(self.root.name, sleep_cycle))

        timeline = [[] for i in range(sleep_cycle)]
        timeline[0] = [i for i in self.root.target_device]
        timeline[0].append(self.root)
        return timeline
