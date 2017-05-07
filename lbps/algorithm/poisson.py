'''
Save the time for calculation by saving result

sleep_cycle_log = {sha256_key: K}
packet_accu_log = {sha256_key: packet}
'''
import os
import json

from hashlib import sha256
from scipy.stats import poisson


sleep_cycle_log = os.path.abspath('sleep_cycle.json')
packet_accu_log = os.path.abspath('packet_accu.json')

def get_sleep_cycle(lambd, data_threshold, prob_threshold=0.8):

    key = 'lambd={},DATA_TH={},PROB_TH={}'.format(
        lambd, data_threshold, prob_threshold)
    key = sha256(key.encode('utf-8')).hexdigest()
    sleep_cycle = 1
    records = {}

    # check file
    if not os.path.exists(sleep_cycle_log):
        os.mknod(sleep_cycle_log)
    else:
        with open(sleep_cycle_log, 'r') as f:
            records = json.load(f)

    # check records
    if key in records.keys():
        return records[key]
    else:
        while True:
            mu = lambd * sleep_cycle
            prob = [poisson.pmf(i, mu) for i in range(int(data_threshold))]
            skip = False

            for i, p in enumerate(prob):
                if 1 - sum(prob[:i]) < prob_threshold:
                    skip = True
                    break

            if skip: sleep_cycle += 1
            else: break

        with open(sleep_cycle_log, 'w') as f:
            records[key] = sleep_cycle
            json.dump(records, f)
        return sleep_cycle

# FIXME: need test
def get_data_accumulation(lambd, sleep_cycle, prob_threshold=0.8):
    key = 'lambd={},sleep_cycle={},PROB_TH={}'.format(
        lambd, sleep_cycle, prob_threshold)
    key = sha256(key.encode('utf-8')).hexdigest()
    packet = 0
    records = {}

    # check file
    if not os.path.exists(packet_accu_log):
        os.mknod(packet_accu_log)
    else:
        with open(packet_accu_log, 'r') as f:
            records = json.load(f)


    # check records
    if key in records.keys():
        return records[key]
    else:
        while True:
            mu = lambd * sleep_cycle
            prob = [poisson.pmf(i, mu) for i in range(packet)]
            skip = False

            for i, p in enumerate(prob):
                if sum(prob[:i]) > prob_threshold:
                    skip = True
                    break

            if skip: packet += 1
            else: break

        with open(packet_accu_log, 'w') as f:
            records[key] = sleep_cycle
            json.dump(records, f)
        return packet
