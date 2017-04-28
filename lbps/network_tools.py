import sys
import logging

sys.path.append('..')
from lbps.structure.base_station import BaseStation
from lbps.structure.relay_node import RelayNode
from lbps.structure.user_equipment import UserEquipment
from src import tdd
from src.traffic import VoIP
from src.bearer import Bearer


class LBPSNetwork(object):
    '''
    *relay_users represent the number of relay ues for each relay
    '''
    def __init__(self, backhaul_CQI, access_CQI, *relay_users):
        self.root = self.network_setup(backhaul_CQI, access_CQI, *relay_users)
        self.traffic = None

    def network_setup(self, backhaul_CQI, access_CQI, *relay_users):
        bs = BaseStation()
        for rue in relay_users:

            # backhaul
            rn = RelayNode()
            bs.connect_to(rn, CQI=backhaul_CQI, flow=VoIP())
            logging.debug('builded backhaul network, current lambd %d' % (bs.lambd))

            # access
            assert isinstance(rue, int)
            for i in range(rue):
                rn.connect_to(UserEquipment(), CQI=access_CQI, flow=VoIP())
            logging.debug('%s builded access bearer with %d user' % (rn.name, rue))
            logging.debug('builded access network, current lambd %g' % (bs.lambd))

        logging.debug('%s builded backhaul bearer with %d relays' % (bs.name, len(relay_users)))
        logging.info(
            'Builded network with backhaul lambd %g and access lambd %g' %
            (bs.lambd, sum([_.lambd for _ in bs.target_device])))

        return bs

    def simulate(self, simulation_time):
        self.traffic = self.root.simulate_timeline(simulation_time)
        logging.info('Generate {} packet for simulation time {} ms'.format(
            sum([len(v) for v in self.traffic.values()]), simulation_time))

    def set_tdd_configuration(self, n_hop, config_index):
        assert isinstance(n_hop, str)
        if n_hop == 'one-hop':
            config = tdd.one_hop_config[config_index]
            self.root.tdd_config = config
            for ue in self.root.target_device:
                ue.tdd_config = config

        elif n_hop == 'two-hop':
            # FIXME: considering two-hop and direct link mixed
            config = tdd.two_hop_config[config_index]
            self.root.tdd_config = config['backhaul']
            for rn in self.root.target_device:
                rn.backhaul.tdd_config = config['backhaul']
                rn.access.tdd_config = config['access']
                for ue in rn.access.target_device:
                    ue.tdd_config = config['access']

            logging.info('Set two-hop tdd configuration %d' % (config_index))
            logging.debug('backhaul configuration\t%s' % (str(config['backhaul'])))
            logging.debug('access configuration\t\t%s' % (str(config['access'])))

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

        logging.info('Set network division mode in %s' % (mode))
