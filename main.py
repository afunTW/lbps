import os
import lbps
import json
import logging

from datetime import datetime
from lbps import network_tools as nt
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
    if not os.path.exists(filepath):
        with open(filepath, 'w') as f:
            json.dump([], f)
            logging.info('Creating file %s' % filepath)

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
        # ,(lbps.ALGORITHM_LBPS_SPLIT, lbps.ALGORITHM_LBPS_TOPDOWN)
        # ,(lbps.ALGORITHM_LBPS_MERGE, lbps.ALGORITHM_LBPS_TOPDOWN)
        # ,(lbps.ALGORITHM_LBPS_MINCYCLE, lbps.ALGORITHM_LBPS_AGGR)
        # ,(lbps.ALGORITHM_LBPS_MINCYCLE, lbps.ALGORITHM_LBPS_SPLIT)
        # ,(lbps.ALGORITHM_LBPS_MERGECYCLE, lbps.ALGORITHM_LBPS_MERGE)
    ]

    mapping = [
        (lbps.MAPPING_M2, lbps.MAPPING_M2)
        ,(lbps.MAPPING_M3, lbps.MAPPING_M3)
        ,(lbps.MAPPING_INTEGRATED, lbps.MAPPING_M2)
        ,(lbps.MAPPING_INTEGRATED, lbps.MAPPING_M3)
    ]

    equal_load_network = nt.LBPSNetwork(15, 15, 40, 40, 40, 40, 40, 40)
    equal_load_network.set_tdd_configuration(lbps.MODE_TWO_HOP, 17)
    equal_load_network.set_division_mode('TDD')

    for i in range(12):
        target_lambda = VoIP().lambd*(i+1)
        equal_load_network.set_bearer_lambd(target_lambda)
        equal_load_network.simulate(simulation_time)

        for algorithm in proposed_lbps:
            for method in mapping:
                equal_load_network.apply(algorithm, mapping=method)
                equal_load_network.run(equal_load_network.demo_timeline)

                filename = get_filename(algorithm, method)
                filename = os.path.join(outdir, filename)
                exist_json(filename)

                with open(filename, 'r') as f:
                    metadata = json.load(f)

                metadata.append(equal_load_network.demo_summary)

                with open(filename, 'w+') as f:
                    json.dump(metadata, f, indent=2)

if __name__ == '__main__':

    now = datetime.now()
    logname = './log/%s.log' % now.strftime('%Y%m%d')
    outdir = 'metadata' + '/' + now.strftime('%Y%m%d')
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
