import sys
import lbps
import logging

sys.path.append('..')
from lbps.structure.base_station import BaseStation
from lbps.structure.relay_node import RelayNode
from lbps.structure.user_equipment import UserEquipment

from lbps.algorithm import basic as lbps_basic
from lbps.algorithm import topdown as lbps_topdown
from lbps.algorithm import bottomup as lbps_bottomup

from lbps.tdd import basic as mapping_basic
from lbps.tdd import two_hop as mapping_2hop

from src import tdd
from src.traffic import VoIP
from src.bearer import Bearer


class LBPSNetwork(object):
    '''
    *relay_users represent the number of relay ues for each relay
    '''
    def __init__(self, backhaul_CQI, access_CQI, *relay_users):
        self.__root = None
        self.__rns = []
        self.__traffic = None
        self.__map_pattern = None
        self.demo = None

        # flag
        self.__hop = None
        self.__method = None
        self.__division = None
        self.__tdd_config = None

        # constructor
        self.network_setup(backhaul_CQI, access_CQI, *relay_users)

    @property
    def root(self):
        return self.__root

    @property
    def builded_rn(self):
        return self.__rns

    @property
    def traffic(self):
        return self.__traffic

    def network_setup(self, backhaul_CQI, access_CQI, *relay_users):
        self.__root = BaseStation()

        for i in range(len(relay_users)):
            rn = RelayNode()
            self.__rns.append(rn)

        self.build_connection(backhaul_CQI, access_CQI, *relay_users)

    def build_connection(self, backhaul_CQI, access_CQI, *relay_users):
        assert len(relay_users) == len(self.__rns)

        # build connection
        for rn_index, rue in enumerate(relay_users):
            assert isinstance(rue, int)
            rn = self.__rns[rn_index]
            for i in range(rue):
                rn.connect_to(UserEquipment(), CQI=access_CQI, flow=VoIP())
            self.root.connect_to(rn, CQI=backhaul_CQI, flow=VoIP())

        # update backhaul lambda
        for bearer in self.root.bearer:
            bearer.flow.lambd = bearer.destination.access.lambd

        logging.debug(
            '{} builded {} backhaul bearer with {} relays'.format(
            self.root.name, len(self.root.bearer), len(relay_users)))
        logging.info(
            'Builded network with backhaul lambd {} and access lambd {}'.format(
                self.root.lambd, [_.lambd for _ in self.root.target_device]))

    def simulate(self, simulation_time):
        self.__traffic = self.root.simulate_timeline(simulation_time)
        logging.info('Generate {} packet for simulation time {} ms'.format(
            sum([len(v) for v in self.traffic.values()]), simulation_time))

    def set_bearer_lambd(self, lambd):

        # update access lambda
        for rn in self.__rns:
            for bearer in rn.access.bearer:
                bearer.flow.lambd = lambd

        # update backhaul lambda
        for bearer in self.root.bearer:
            bearer.flow.lambd = bearer.destination.access.lambd

        logging.info(
            'Builded network with backhaul lambd {} and access lambd {}'.format(
                self.root.lambd, [_.lambd for _ in self.root.target_device]))

    def set_tdd_configuration(self, n_hop, config_index):
        if n_hop == lbps.MODE_ONE_HOP:
            config = tdd.one_hop_config[config_index]
            self.root.tdd_config = config
            for ue in self.root.target_device:
                ue.tdd_config = config
            self.__hop = lbps.MODE_ONE_HOP
            self.__tdd_config = config

        elif n_hop == lbps.MODE_TWO_HOP:
            # FIXME: considering two-hop and direct link mixed
            config = tdd.two_hop_config[config_index]
            self.root.tdd_config = config['backhaul']
            for rn in self.root.target_device:
                rn.backhaul.tdd_config = config['backhaul']
                rn.access.tdd_config = config['access']
                for ue in rn.access.target_device:
                    ue.tdd_config = config['access']

            self.__hop = lbps.MODE_TWO_HOP
            self.__tdd_config = config
            logging.info('Set two-hop tdd configuration %d' % (config_index))
            logging.debug('backhaul configuration {}'.format(str(config['backhaul'])))
            logging.debug('access configuration {}'.format(str(config['access'])))

        else:
            logging.warning('No %s config method' % (n_hop))

    def set_division_mode(self, mode):
        assert isinstance(mode, str), 'given mode is not string'
        assert mode in ['FDD', 'TDD'], 'given mode is not FDD either TDD'

        self.root.division_mode = mode
        for rn in self.root.target_device:
            rn.backhaul.division_mode = mode
            rn.access.division_mode = mode
            for ue in rn.access.target_device:
                ue.division_mode = mode

        self.__division = mode
        logging.info('Set network division mode in %s' % (mode))

    def run(self, method, mapping=None):
        '''
        wrapper of lbps/DRX algorithm implementation
        '''
        assert isinstance(method, (tuple, int))
        if not mapping and not self.__division:
            self.set_division_mode('TDD')

        logging.info('Running algorithm {}'.format(method))

        # one hop lbps algorithm
        if isinstance(method, int):
            logging.info(' - apply as one hop algorithm')
            if method == lbps.ALGORITHM_LBPS_AGGR:
                aggr = lbps_basic.Aggr(self.root)
                self.demo = aggr.run()
                self.__method = method
            elif method == lbps.ALGORITHM_LBPS_SPLIT:
                split = lbps_basic.Split(self.root)
                self.demo = split.run()
                self.__method = method
            elif method == lbps.ALGORITHM_LBPS_MERGE:
                merge = lbps_basic.Merge(self.root)
                self.demo = merge.run()
                self.__method = method
            else:
                logging.warning('{} lbps algorithm not found'.format(method))

        # two hops lbps algorithm
        elif isinstance(method, tuple) and len(method) == 2:
            logging.info(' - apply as two hop algorithm')
            backhaul_method, access_method = method
            if access_method == lbps.ALGORITHM_LBPS_TOPDOWN:
                td = lbps_topdown.TopDown(self.__root)
                self.demo = td.run(backhaul_method)
                self.__method = method
            elif backhaul_method == lbps.ALGORITHM_LBPS_MINCYCLE:
                if access_method == lbps.ALGORITHM_LBPS_AGGR:
                    bu = lbps_bottomup.MinCycleAggr(self.__root)
                    self.demo = bu.run()
                elif access_method == lbps.ALGORITHM_LBPS_SPLIT:
                    bu = lbps_bottomup.MinCycleSplit(self.__root)
                    self.demo = bu.run()
            elif backhaul_method == lbps.ALGORITHM_LBPS_MERGECYCLE:
                if access_method == lbps.ALGORITHM_LBPS_MERGE:
                    bu = lbps_bottomup.MergeCycleMerge(self.__root)
                    self.demo = bu.run()

        # mapping
        if self.demo and self.__method and self.__division == 'TDD':
            if self.__hop == lbps.MODE_ONE_HOP:
                if mapping == lbps.MAPPING_M1:
                    M1 = mapping_basic.one2all(self.__tdd_config)
                    self.__map_pattern = M1.pattern
                elif mapping == lbps.MAPPING_M2:
                    M2 = mapping_basic.continuous(self.__tdd_config)
                    self.__map_pattern = M2.pattern
                elif mapping == lbps.MAPPING_M3:
                    M3 = mapping_basic.one2one_first(self.__tdd_config)
                    self.__map_pattern = M3.pattern
                else:
                    logging.warning('{} mapping not found')
            elif self.__hop == lbps.MODE_TWO_HOP:
                if mapping == lbps.MAPPING_INTEGRATED_M2:
                    b_timeline, a_timeline = self.demo
                    mapper = mapping_2hop.IntegratedTwoHop(
                        self.__root, b_timeline, a_timeline, lbps.MAPPING_M2)
                    self.demo = mapper.mapping()
                elif mapping == lbps.MAPPING_INTEGRATED_M3:
                    b_timeline, a_timeline = self.demo
                    mapper = mapping_2hop.IntegratedTwoHop(
                        self.__root, b_timeline, a_timeline, lbps.MAPPING_M3)
                    self.demo = mapper.mapping()
