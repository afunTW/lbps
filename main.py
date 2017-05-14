import os
import lbps
import logging

from datetime import datetime
from pprint import pprint
from lbps import network_tools as nt
from lbps.algorithm import basic


def main(simulation_time):
    # hot_spot_network = network_setup(15, 15, 96, 96, 12, 12, 12, 12)
    equal_load_network = nt.LBPSNetwork(15, 15, 40, 40, 40, 40, 40, 40)
    equal_load_network.set_tdd_configuration(lbps.MODE_TWO_HOP, 17)
    equal_load_network.set_division_mode('TDD')
    equal_load_network.simulate(simulation_time)
    equal_load_network.run((lbps.ALGORITHM_LBPS_MINCYCLE, lbps.ALGORITHM_LBPS_SPLIT))

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
        format='%(asctime)s %(filename)s:L%(lineno)s [%(levelname)8s] %(message)s',
        datefmt='%b %d %H:%M:%S',
        filename=logname
        )

    stdout = logging.StreamHandler()
    stdout_format = logging.Formatter(
        '%(asctime)s %(filename)s:L%(lineno)s [%(levelname)8s] %(message)s',
        '%b %d %H:%M:%S')
    stdout.setFormatter(stdout_format)
    stdout.setLevel(logging.DEBUG)
    logging.getLogger().addHandler(stdout)

    try:
        rn_count = 6
        ue_count = 240
        simulation_time = 10000
        main(simulation_time)
    except Exception as e:
        logging.exception(e)
