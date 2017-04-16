import os
import logging

from datetime import datetime
from pprint import pprint
from lbps import network_tools as nt
from lbps.algorithm import basic


rn_count = 6
ue_count = 240
simulation_time = 10000

def main():
    equal_load_network = nt.network_setup(15, 15, 40, 40, 40, 40, 40, 40)
    nt.set_tdd_configuration(equal_load_network, 'two-hop', 17)
    # hot_spot_network = network_setup(15, 15, 96, 96, 12, 12, 12, 12)

if __name__ == '__main__':
    now = datetime.now()
    logname = './log/%s.log' % now.strftime('%Y%m%d')
    logdir = '/'.join(logname.split('/')[:-1])

    if not os.path.exists(logdir):
        logdir = os.path.abspath(logdir)
        os.makedirs(logdir)
        logging.info('Creating directory %s' % logdir)

    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s [%(levelname)8s] %(message)s',
        datefmt='%b %d %H:%M:%S',
        filename=logname
        )

    stdout = logging.StreamHandler()
    stdout_format = logging.Formatter(
        '%(asctime)s [%(levelname)8s] %(message)s',
        '%b %d %H:%M:%S')
    stdout.setFormatter(stdout_format)
    stdout.setLevel(logging.DEBUG)
    logging.getLogger().addHandler(stdout)

    try:
        main()
    except Exception as e:
        logging.exception(e)
