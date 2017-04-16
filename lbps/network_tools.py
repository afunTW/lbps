import sys
import logging

sys.path.append('..')
from lbps.structure.base_station import BaseStation as BS
from lbps.structure.relay_node import RelayNode as RN
from lbps.structure.user_equipment import UserEquipment as UE
from src import tdd
from src.traffic import VoIP
from src.bearer import Bearer


def network_setup(backhaul_CQI, access_CQI, *relay_users):
    '''
    *relay_users represent the number of relay ues for each relay
    '''

    bs = BS()

    for rue in relay_users:

        # backhaul
        rn = RN()
        bs.connect_to(rn, CQI=backhaul_CQI, flow=VoIP())
        logging.debug('builded backhaul network, current lambd %d' % (bs.lambd))

        # access
        assert isinstance(rue, int)
        for i in range(rue):
            rn.connect_to(UE(), CQI=access_CQI, flow=VoIP())
        logging.debug('%s builded access bearer with %d user' % (rn.name, rue))
        logging.debug('builded access network, current lambd %g' % (bs.lambd))

    logging.debug('%s builded backhaul bearer with %d relays' % (bs.name, len(relay_users)))
    logging.info(
        'Builded network with backhaul lambd %g and access lambd %g' %
        (bs.lambd, sum([_.lambd for _ in bs.target_device])))
    return bs

def simulation(base_station, simulation_time):
    assert isinstance(base_station, BS)
    return base_station.simulate_timeline(simulation_time)

def set_tdd_configuration(base_station, n_hop, config_index):
    assert isinstance(base_station, BS)
    assert isinstance(n_hop, str)

    if n_hop == 'one-hop':
        config = tdd.one_hop_config[config_index]
        base_station.tdd_config = config
        for ue in base_station.target_device:
            ue.tdd_config = config

    elif n_hop == 'two-hop':
        # FIXME: considering two-hop and direct link mixed
        config = tdd.two_hop_config[config_index]
        base_station.tdd_config = config['backhaul']
        for rn in base_station.target_device:
            rn.backhaul.tdd_config = config['backhaul']
            rn.access.tdd_config = config['access']
            for ue in rn.access.target_device:
                ue.tdd_config = config['access']

        logging.info('Set two-hop tdd configuration %d' % (config_index))
        logging.debug('backhaul configuration\t%s' % (str(config['backhaul'])))
        logging.debug('access configuration\t\t%s' % (str(config['access'])))

    else:
        logging.warning('No %s config method' % (n_hop))
