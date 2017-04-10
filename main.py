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

def main():
    global rn_count, ue_count

    # build equal load network
    base_station = BS()
    relay_nodes = [RN() for i in range(rn_count)]
    user_nodes = [UE() for i in range(ue_count)]
    backhaul_bearear = [
        Bearer(
            base_station,
            r.backhaul,
            CQI=15,
            flow=VoIP()
            ).build_connection() for r in relay_nodes
    ]

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
