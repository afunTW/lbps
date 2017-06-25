import os
import lbps
import json
import logging

from datetime import datetime
from lbps import network_tools as nt
from lbps import drx
from lbps.algorithm import basic
from src.traffic import VoIP


def get_filename(algorithm, mapping):
    def __lbps_name(x):
        if x == lbps.ALGORITHM_LBPS_AGGR: return 'aggr'
        elif x == lbps.ALGORITHM_LBPS_SPLIT: return 'split'
        elif x == lbps.ALGORITHM_LBPS_MERGE: return 'merge'
        elif x == lbps.ALGORITHM_LBPS_MINCYCLE: return 'mincycle'
        elif x == lbps.ALGORITHM_LBPS_MERGECYCLE: return 'mergecycle'
        elif x == lbps.ALGORITHM_LBPS_TOPDOWN: return 'topdown'
        else: return ''

    def __mapping_name(x):
        if x == lbps.MAPPING_M1: return 'M1'
        elif x == lbps.MAPPING_M2: return 'M2'
        elif x == lbps.MAPPING_M3: return 'M3'
        elif x == lbps.MAPPING_INTEGRATED: return 'proposed'
        else: return ''

    name = '_'.join([
        __lbps_name(algorithm[0]), __lbps_name(algorithm[1]),
        __mapping_name(mapping[0]), __mapping_name(mapping[1])])

    return ''.join([name, '.json'])

def exist(dir_path):
    if not os.path.exists(dir_path):
        dir_path = os.path.abspath(dir_path)
        os.makedirs(dir_path)

def exist_json(filepath):
    directory = os.sep.join(filepath.split(os.sep)[:-1])
    exist(directory)
    if not os.path.exists(filepath):
        with open(filepath, 'w') as f:
            json.dump([], f)
            logging.info('Creating file %s' % filepath)

def save_json(summary, filename, dirname):
    filename = os.path.join(dirname, filename)
    exist_json(filename)

    with open(filename, 'r') as f:
        metadata = json.load(f)
        metadata.append(summary)

    with open(filename, 'w+') as f:
            json.dump(metadata, f, indent=2)

def run_drx(network, drx_instance, dirname):
    logging.info('parent id {}'.format(os.getppid()))
    logging.info('process id {}'.format(os.getpid()))
    drx_instance.run(network.traffic)
    filename = drx_instance.name + '.json'
    save_json(drx_instance.demo_summary, filename, dirname)

def run_lbps(network, algorithm, method, dirname):
    logging.info('parent id {}'.format(os.getppid()))
    logging.info('process id {}'.format(os.getpid()))
    network.apply(algorithm, mapping=method)
    network.run(network.demo_timeline)
    filename = get_filename(algorithm, method)
    save_json(network.demo_summary, filename, dirname)

def main(simulation_time):
    '''
    ======================================================================
        Simulate the lbps netwowrk with proposed scheduling algorithm

        # network
        equal load network apply RUEs distribution in 40,40,40,40,40,40
        hot spot network apply RUEs distribution in 96,96,12,12,12,12

        # lbps proposed algorithm
        (lbps.ALGORITHM_LBPS_AGGR, lbps.ALGORITHM_LBPS_TOPDOWN)
        (lbps.ALGORITHM_LBPS_SPLIT, lbps.ALGORITHM_LBPS_TOPDOWN)
        (lbps.ALGORITHM_LBPS_MERGE, lbps.ALGORITHM_LBPS_TOPDOWN)
        (lbps.ALGORITHM_LBPS_MINCYCLE, lbps.ALGORITHM_LBPS_AGGR)
        (lbps.ALGORITHM_LBPS_MINCYCLE, lbps.ALGORITHM_LBPS_SPLIT)
        (lbps.ALGORITHM_LBPS_MERGECYCLE, lbps.ALGORITHM_LBPS_MERGE)

        # lbps proposed mapping algorithm
        (lbps.MAPPING_INTEGRATED, lbps.MAPPING_M2),
        (lbps.MAPPING_INTEGRATED, lbps.MAPPING_M3)
    ======================================================================
    '''
    proposed_lbps = [
        (lbps.ALGORITHM_LBPS_AGGR, lbps.ALGORITHM_LBPS_TOPDOWN)
        ,(lbps.ALGORITHM_LBPS_SPLIT, lbps.ALGORITHM_LBPS_TOPDOWN)
        ,(lbps.ALGORITHM_LBPS_MERGE, lbps.ALGORITHM_LBPS_TOPDOWN)
        ,(lbps.ALGORITHM_LBPS_MINCYCLE, lbps.ALGORITHM_LBPS_AGGR)
        ,(lbps.ALGORITHM_LBPS_MINCYCLE, lbps.ALGORITHM_LBPS_SPLIT)
        ,(lbps.ALGORITHM_LBPS_MERGECYCLE, lbps.ALGORITHM_LBPS_MERGE)
    ]

    mapping = [
        (lbps.MAPPING_M2, lbps.MAPPING_M2)
        ,(lbps.MAPPING_M3, lbps.MAPPING_M3)
    ]

    networks = {
        'equal_load': nt.LBPSNetwork(['H'], ['M'], 40, 40, 40, 40, 40, 40),
        'hot_spot': nt.LBPSNetwork(['H'], ['M'], 96, 96, 12, 12, 12, 12)
    }

    for t, network in networks.items():
        dirname = os.path.join(outdir, t)
        network = nt.LBPSNetwork(['H'], ['M'], 40, 40, 40, 40, 40, 40)
        network.set_tdd_configuration(lbps.MODE_TWO_HOP, 17)
        network.set_division_mode('TDD')

        for i in range(12):
            target_lambda = VoIP().lambd*(i+1)
            network.set_bearer_lambd(target_lambda)
            network.simulate(simulation_time)
            Std_DRX_1 = drx.DRX(network.root, 40, 1, 80, 160, 'Std_DRX_1')
            Std_DRX_2 = drx.DRX(network.root, 40, 1, 160, 320, 'Std_DRX_2')

            # drx subprocess
            for std_drx in [Std_DRX_1, Std_DRX_2]:
                run_drx(network, std_drx, dirname)

            # lbps subprocess
            for algorithm in proposed_lbps:
                for method in mapping:
                    run_lbps(network, algorithm, method, dirname)


if __name__ == '__main__':

    now = datetime.now()
    logname = './log/%s.log' % now.strftime('%Y%m%d')
    outdir = 'metadata'
    exist('/'.join(logname.split('/')[:-1]))
    exist(outdir)
    outdir = os.path.abspath(outdir)

    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s %(filename)s:L%(lineno)s [%(levelname)8s] %(message)s',
        datefmt='%b %d %H:%M:%S',
        filename=logname
        )
    stdout = logging.StreamHandler()
    stdout_format = logging.Formatter(
        '%(asctime)s %(filename)-16s:L%(lineno)3s [%(levelname)8s] %(message)s',
        '%b %d %H:%M:%S')
    stdout.setFormatter(stdout_format)
    stdout.setLevel(logging.INFO)
    logging.getLogger().addHandler(stdout)

    try:
        rn_count = 6
        ue_count = 240
        simulation_time = 10000
        main(simulation_time)
    except Exception as e:
        logging.exception(e)
