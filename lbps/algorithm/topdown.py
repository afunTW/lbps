import sys
import logging

sys.path.append('../..')
from math import ceil
from lbps.__init__ import *
from lbps.algorithm import basic


class TopDown(basic.BaseLBPS):
    '''
    Two hop lbps algorithm
    '''
    def __init__(self, root):
        super().__init__(root)
        self.__backhaul_timeline = None
        self.__access_timeline = None

    @property
    def backhaul_timeline(self):
        return self.__backhaul_timeline

    @backhaul_timeline.setter
    def backhaul_timeline(self, method):
        if method == ALGORITHM_LBPS_AGGR:
            aggr = basic.Aggr(self.root)
            self.__backhaul_timeline = aggr.run()
        elif method == ALGORITHM_LBPS_SPLIT:
            split = basic.Split(self.root)
            self.__backhaul_timeline = split.run()
        elif method == ALGORITHM_LBPS_MERGE:
            merge = basic.Merge(self.root)
            self.__backhaul_timeline = merge.run()
        else:
            logging.error('Please given one of basic lbps algorithm for backhaul')

    @property
    def access_timeline(self):
        return self.__access_timeline

    def run(self, backhaul_method):
        '''
        backhaul awake: #awake_times for rn in backhaul
        access awake: #awake_times for rn in access for passing data from backhaul
        access K: access sleep cycle for each rn
        schedulability: schedulability for rn in access
        '''
        self.backhaul_timeline = backhaul_method
        assert self.backhaul_timeline
        backhaul_K = len(self.backhaul_timeline)

        rn_info = {}
        for rn in self.root.target_device:
            backhaul_awake = sum([1 for t in self.backhaul_timeline if rn in t])
            access_awake = ceil(self.root.lbps_capacity/rn.access.lbps_capacity)

            rn_info[rn] = {
            'backhaul_awake': backhaul_awake,
            'access_awake': access_awake,
            'access_K': int(backhaul_K/backhaul_awake),
            'schedulability': access_awake < int(backhaul_K/backhaul_awake)
            }

        if not all([rn_info[rn]['schedulability'] for rn in self.root.target_device]):
            backhaul_failed = [rn for rn in self.root.target_device]
            backhaul_failed.append(self.root)
            backhaul_failed = [backhaul_failed] * backhaul_K
            access_failed = [ ue
                for rn in self.root.target_device
                for ue in rn.access.target_device]
            access_failed += self.root.target_device
            access_failed = [access_failed] * backhaul_K
            self.__backhaul_timeline = backhaul_failed
            self.__access_timeline = access_failed
            logging.warning(' - top down algorithm failed, all awake')
        else:
            access_timeline = [[] for i in range(backhaul_K)]
            for rn in self.root.target_device:
                rn_access_timeline = [ue for ue in rn.access.target_device]
                rn_access_timeline.append(rn)

                for begin in range(0, backhaul_K, rn_info[rn]['access_K']):
                    for TTI in range(rn_info[rn]['access_awake']):
                        access_timeline[begin + TTI] += rn_access_timeline
            self.__access_timeline = access_timeline

        return (self.backhaul_timeline, self.access_timeline)
