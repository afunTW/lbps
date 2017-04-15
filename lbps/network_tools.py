import sys
import logging

sys.path.append('..')
from lbps.structure.base_station import BaseStation as BS
from lbps.structure.relay_node import RelayNode as RN
from lbps.structure.user_equipment import UserEquipment as UE
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
