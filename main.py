import os
import logging

from datetime import datetime
from lbps.structure import base_station
from lbps.structure import relay_node
from lbps.structure import user_equipment
from lbps.algorithm import basic


if __name__ == '__main__':
    now = datetime.now()
    logname = './log/%s.log' % now.strftime('%Y%m%d')
    logdir = '/'.join(logname.split('/')[:-1])

    if not os.path.exists(logdir):
        logdir = os.path.abspath(logdir)
        os.makedirs(logdir)
        logging.info('Creating directory %s' % logdir)

    logging.getLogger().addHandler(logging.StreamHandler())
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)-8s] %(message)s',
        datefmt='%b %d %H:%M:%S',
        filename=logname
        )
