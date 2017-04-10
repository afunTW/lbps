import os
import logging

from datetime import datetime
from pprint import pprint
from lbps.structure.base_station import BaseStation as BS
from lbps.structure.relay_node import RelayNode as RN
from lbps.structure.user_equipment import UserEquipment as UE
from lbps.algorithm import basic
from src.traffic import VoIP
from src.bearer import Bearer


rn_count = 6
ue_count = 240

# relay_users represent the number of relay ues for each relay
def network_setup(backhaul_CQI, access_CQI, *relay_users):
    bs = BS()

    for rue in relay_users:
        # backhaul
        rn = RN()
        Bearer(
            bs, rn.backhaul, CQI=backhaul_CQI, flow=VoIP()
            ).build_connection()

        # access
        assert isinstance(rue, int)
        for i in range(rue):
            Bearer(
                rn.access, UE(), CQI=access_CQI, flow=VoIP()
                ).build_connection()

    return bs

def main():
    global rn_count, ue_count
    # equal_load_network = network_setup(15, 15, 40, 40, 40, 40, 40, 40)
    hot_spot_network = network_setup(15, 15, 96, 96, 12, 12, 12, 12)

if __name__ == '__main__':
    now = datetime.now()
    logname = './log/%s.log' % now.strftime('%Y%m%d')
    logdir = '/'.join(logname.split('/')[:-1])

    if not os.path.exists(logdir):
        logdir = os.path.abspath(logdir)
        os.makedirs(logdir)
        logging.info('Creating directory %s' % logdir)

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)8s] %(message)s',
        datefmt='%b %d %H:%M:%S',
        filename=logname
        )
    logging.getLogger().addHandler(logging.StreamHandler())

    try:
        main()
    except Exception as e:
        logging.exception(e)
