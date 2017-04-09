import sys
import logging

sys.path.append('../..')
from lbps.structure import device as dev
from lbps.algorithm import poisson


def get_load(device):
    avg_pkt_size = get_packet_size(device.bearer)
    return device.lambd*avg_pkt_size/device.lbps_capacity

def get_packet_size(bearer_buffer):
    total_pkt_size = sum([b.flow.packet_size for b in bearer_buffer])
    return total_pkt_size/len(bearer_buffer)

def get_data_threshold(capacity, packet_size, percentage=0.8):
    return capacity/packet_size*percentage

def aggr(device):
    try:
        assert isinstance(device, dev.OneHopDevice),\
        'given device is not fit in lbps structure'

        if isinstance(device, dev.TwoHopDevice):
            device = device.access

        capacity = device.lbps_capacity
        packet_size = get_packet_size(device.bearer)
        data_threshold = get_data_threshold(capacity, packet_size)
        logging.info('running aggr under %f load' % get_load(device))

        # core
        sleep_cycle = poisson.get_sleep_cycle(device.lambd, data_threshold)
        logging.info('%s sleep cycle: %d' % (device.name, sleep_cycle))

        timeline = [[] for i in range(sleep_cycle)]
        timeline[0] = [i for i in device.target_device]
        timeline[0].append(device)
        timeline[0] = sorted(timeline[0], key=lambda d: d.name)
        return timeline

    except Exception as e:
        logging.exception(e)