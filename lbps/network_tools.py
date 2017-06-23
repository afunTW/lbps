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


class LBPSWrapper(object):
    @staticmethod
    def all_devices(root, *device_type):
        try:

            flatten = lambda x: [j for i in x for j in i]
            devices = {
                rn: rn.access.target_device
                for rn in root.target_device
            }
            devices = list(devices.keys()) + flatten(list(devices.values()))
            devices.append(root)

            if not device_type: return devices
            new_devices = []
            for device in devices:
                if isinstance(device, device_type): new_devices.append(device)
            return new_devices

        except Exception as e:
            logging.exception(e)

    def clear_env(self, root):
        devices = self.all_devices(
            root,
            BaseStation, RelayNode, UserEquipment)
        for d in devices:
            if isinstance(d, RelayNode):
                d.backhaul.buffer = []
                d.access.buffer = []
            else:
                d.buffer = []

class LBPSNetwork(LBPSWrapper):
    '''
    *relay_users represent the number of relay ues for each relay
    '''
    def __init__(self, backhaul_CQI, access_CQI, *relay_users):
        self.__root = None
        self.__rns = []
        self.__traffic = None
        self.demo_timeline = None
        self.demo_meta = None
        self.demo_summary = None

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

    def __basic_mapper(self, mapping_config, tdd_config):
        basic_mapping = {
            lbps.MAPPING_M1: mapping_basic.one2all(tdd_config),
            lbps.MAPPING_M2: mapping_basic.continuous(tdd_config),
            lbps.MAPPING_M3: mapping_basic.one2one_first(tdd_config)
        }
        assert mapping_config in basic_mapping.keys()
        return basic_mapping[mapping_config]

    def __transmit_packet(self, TTI, timeline, metadata=None, flush=False):
        '''
        check the condition of packet transmitting
        * TDD configuration
        * capacity
        * user-defined parameter, "flush"
        * LBPS prediction
        * force-awake
        * inband
        '''
        def __transmit(pkt, src, dest, cap):
            dest.buffer.append(pkt)
            src.buffer.remove(pkt)
            return cap-pkt['size']

        def __stuck(metadata, src):
            metadata[src]['stuck'] = True
            metadata[src]['force-awake'] += 1

        def __sleep_or_awake(metadata, src, time_slot):
            if metadata[src]['stuck'] or src in time_slot:
                metadata[src]['awake'] += 1
            else:
                metadata[src]['sleep'] += 1

        if not metadata:
            metadata = {
                d: {
                    'sleep': 0,
                    'awake': 0,
                    'delay': 0,
                    'stuck': False,
                    'force-awake': 0
                } for d in self.all_devices(self.root, RelayNode, UserEquipment)
            }

        # backhaul
        backhaul_activate_rn = []
        if self.__tdd_config['backhaul'][TTI%10] == 'D':

            # transmission
            available_cap = self.root.wideband_capacity
            for pkt in self.root.buffer:
                rn = pkt['device'].ref_access
                if available_cap < pkt['size']: break
                if flush or rn in timeline[TTI] or metadata[rn]['stuck']:
                    backhaul_activate_rn.append(rn)
                    available_cap = __transmit(
                        pkt, self.root, rn.backhaul, available_cap)

            # metadata
            if not flush:
                stuck_rn = [pkt['device'].ref_access for pkt in self.root.buffer]
                for rn in self.root.target_device:
                    if rn in stuck_rn: __stuck(metadata, rn)
                    if rn in backhaul_activate_rn:
                        metadata[rn]['awake'] += 1

                        # inband
                        _ = [
                            __sleep_or_awake(metadata, ue, timeline[TTI])
                            for ue in rn.access.target_device
                        ]

        # access
        if self.__tdd_config['access'][TTI%10] == 'D':
            for rn in self.root.target_device:
                if rn in backhaul_activate_rn: continue
                if flush or rn in timeline[TTI] or metadata[rn]['stuck']:
                    available_cap = rn.access.wideband_capacity
                    activate_ue = []

                    # transmission
                    for pkt in rn.backhaul.buffer:
                        ue = pkt['device']
                        if available_cap < pkt['size']: break
                        if flush or ue in timeline[TTI] or metadata[ue]['stuck']:
                            activate_ue.append(ue)
                            available_cap = __transmit(
                                pkt, rn.backhaul, ue, available_cap)
                            metadata[ue]['delay'] += TTI - pkt['arrival_time']

                    # metadata
                    if not flush:
                        metadata[rn]['awake'] += 1
                        if not rn.backhaul.buffer: __stuck(metadata, rn)
                        else: metadata[rn]['stuck'] = False

                        stuck_ue = [pkt['device'] for pkt in rn.backhaul.buffer]
                        for ue in rn.access.target_device:
                            _ = 'awake' if ue in activate_ue else 'sleep'
                            metadata[ue][_] += 1
                            if ue in stuck_ue: __stuck(metadata, ue)
                            else: metadata[ue]['stuck'] = False

                elif not flush:
                    metadata[rn]['sleep'] += 1
                    _ = [
                        __sleep_or_awake(metadata, ue, timeline[TTI])
                        for ue in rn.access.target_device
                    ]

        return metadata

    def __summary(self, metadata):
        avg = lambda x: sum(x)/len(x)
        fairness = lambda x: sum(x)**2/(len(x)*sum([i**2 for i in x]))

        _all_src = self.all_devices(self.root, RelayNode, UserEquipment)
        _all_rn = self.all_devices(self.root, RelayNode)
        _all_ue = self.all_devices(self.root, UserEquipment)
        _rn_pse = [metadata[d]['sleep'] for d in _all_rn]
        _ue_pse = [metadata[d]['sleep'] for d in _all_ue]
        _ue_delay = [metadata[d]['delay'] for d in _all_ue]
        _received_pkts = sum([len(ue.buffer) for ue in _all_ue])
        summary = {}

        summary['rn-pse'] = round(avg(_rn_pse), 2)
        summary['ue-pse'] = round(avg(_ue_pse), 2)
        summary['ue-delay'] = round(sum(_ue_delay)/_received_pkts, 2)
        summary['pse-fairness'] = round(fairness(_ue_pse), 2)
        summary['delay-fairness'] = round(fairness(_ue_delay), 2)
        return summary

    def __rn_collision(self):
        assert self.demo_timeline is not None
        b_timeline, a_timeline = self.demo_timeline
        assert len(b_timeline) == len(a_timeline)

        _all_rn = self.all_devices(self.root, RelayNode)
        in_both = lambda x, TTI: x in b_timeline[TTI] and x in a_timeline[TTI]
        collision = [
            in_both(rn, TTI)
            for TTI in range(len(b_timeline)) for rn in _all_rn]
        return sum(collision)/len(_all_rn)

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

    def apply(self, method, mapping=None):
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
                self.demo_timeline = aggr.run()
                self.__method = method
            elif method == lbps.ALGORITHM_LBPS_SPLIT:
                split = lbps_basic.Split(self.root)
                self.demo_timeline = split.run()
                self.__method = method
            elif method == lbps.ALGORITHM_LBPS_MERGE:
                merge = lbps_basic.Merge(self.root)
                self.demo_timeline = merge.run()
                self.__method = method
            else:
                logging.warning('{} lbps algorithm not found'.format(method))

        # two hops lbps algorithm
        elif isinstance(method, tuple) and len(method) == 2:
            logging.info(' - apply as two hop algorithm')
            backhaul_method, access_method = method
            if access_method == lbps.ALGORITHM_LBPS_TOPDOWN:
                td = lbps_topdown.TopDown(self.__root)
                self.demo_timeline = td.run(backhaul_method)
                self.__method = method
            elif backhaul_method == lbps.ALGORITHM_LBPS_MINCYCLE:
                if access_method == lbps.ALGORITHM_LBPS_AGGR:
                    bu = lbps_bottomup.MinCycleAggr(self.__root)
                    self.demo_timeline = bu.run()
                elif access_method == lbps.ALGORITHM_LBPS_SPLIT:
                    bu = lbps_bottomup.MinCycleSplit(self.__root)
                    self.demo_timeline = bu.run()
            elif backhaul_method == lbps.ALGORITHM_LBPS_MERGECYCLE:
                if access_method == lbps.ALGORITHM_LBPS_MERGE:
                    bu = lbps_bottomup.MergeCycleMerge(self.__root)
                    self.demo_timeline = bu.run()

        # mapping
        basic_mapping = [lbps.MAPPING_M1, lbps.MAPPING_M2, lbps.MAPPING_M3]
        if self.demo_timeline and mapping and self.__tdd_config and self.__division == 'TDD':

            if self.__hop == lbps.MODE_ONE_HOP:
                if mapping in basic_mapping and isinstance(mapping, int):
                    mapper = self.__basic_mapper(mapping, self.__tdd_config)
                    self.demo_timeline = mapper.map_by_pattern(
                        self.demo_timeline, self.root.simulation_time)
                else:
                    logging.warning('{} mapping not found'.format(mapping))

            elif self.__hop == lbps.MODE_TWO_HOP:
                if isinstance(mapping, tuple) and len(mapping) == 2:
                    b_timeline, a_timeline = self.demo_timeline
                    backhaul_mapping, access_mapping = mapping

                    if (
                        backhaul_mapping == lbps.MAPPING_INTEGRATED and
                        access_mapping in [lbps.MAPPING_M2, lbps.MAPPING_M3]
                    ):
                        mapper = mapping_2hop.IntegratedTwoHop(
                            self.__root, b_timeline, a_timeline, access_mapping)
                        self.demo_timeline = mapper.mapping()

                    elif (
                        backhaul_mapping in basic_mapping and
                        access_mapping in basic_mapping
                    ):
                        backhaul_mapper = self.__basic_mapper(
                            backhaul_mapping, self.__tdd_config['backhaul'].copy())
                        access_mapper = self.__basic_mapper(
                            access_mapping, self.__tdd_config['access'].copy())

                        b_timeline = backhaul_mapper.map_by_pattern(
                            b_timeline, self.root.simulation_time)
                        a_timeline = access_mapper.map_by_pattern(
                            a_timeline, self.root.simulation_time)
                        self.demo_timeline = (b_timeline, a_timeline)

                    else:
                        logging.warning('{} mapping not found'.format(mapping))

        return self.demo_timeline

    def run(self, timeline):
        assert isinstance(timeline, tuple) and len(timeline) == 2
        assert len(timeline[0]) == len(timeline[1])
        assert self.__traffic and self.demo_timeline
        _time = self.root.simulation_time
        _all_src = self.all_devices(self.root, RelayNode, UserEquipment)
        _all_rn = self.all_devices(self.root, RelayNode)
        rn_collision = self.__rn_collision()
        timeline = [timeline[0][i]+timeline[1][i] for i in range(len(timeline[0]))]
        metadata = {
            d: {
                'sleep': 0,
                'awake': 0,
                'delay': 0,
                'stuck': False,
                'force-awake': 0
            } for d in _all_src
        }

        logging.info('* Simulation begin with lambda {} Mbps = load {}'.format(
            self.root.lambd, self.root.load))
        is_downlink = lambda x: b_tdd[TTI%10] == 'D' or a_tdd[TTI%10] == 'D'
        self.clear_env(self.root)

        # simulate packet arriving, TTI = 0 ~ simulation_time
        for TTI, pkt in self.__traffic.items():
            b_tdd = self.__tdd_config['backhaul']
            a_tdd = self.__tdd_config['access']
            if pkt: self.root.buffer += pkt
            if is_downlink(TTI):
                metadata = self.__transmit_packet(TTI, timeline, metadata)
            else:
                for _ in _all_src: metadata[_]['sleep'] += 1

        # out of simulation time
        is_flush = lambda x, y: not x.buffer and all([not _.backhaul.buffer for _ in y])
        TTI = len(self.__traffic)
        while not is_flush(self.root, _all_rn):
            if is_downlink(TTI):
                metadata = self.__transmit_packet(
                    TTI, timeline, metadata, flush=True)
            TTI += 1

        logging.info('* Simulation end with TTI {}'.format(TTI))
        self.demo_meta = metadata

        summary = self.__summary(metadata)
        summary['rn-collision'] = rn_collision
        summary['lambda'] = self.root.lambd
        self.demo_summary = summary
        logging.info('summary = {}'.format(summary))

        return summary
