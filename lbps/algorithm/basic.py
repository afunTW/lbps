import sys
import logging

sys.path.append('../..')
from lbps.structure import device
from lbps.algorithm import poisson


def get_load(root):
    avg_pkt_size = get_packet_size(root.bearer)
    return root.lambd*avg_pkt_size/root.lbps_capacity

def get_packet_size(bearer_buffer):
    total_pkt_size = sum([b.flow.packet_size for b in bearer_buffer])
    return total_pkt_size/len(bearer_buffer)

def get_data_threshold(capacity, packet_size, percentage=0.8):
    return capacity/packet_size*percentage

def aggr(root):
    try:
        assert (
            isinstance(root, device.OneHopDevice) or
            isinstance(root, device.TwoHopDevice)
            ), 'given root is not fit in lbps structure'

        if isinstance(root, device.TwoHopDevice):
            root = root.access

        capacity = root.lbps_capacity
        packet_size = get_packet_size(root.bearer)
        data_threshold = get_data_threshold(capacity, packet_size)
        logging.info('running aggr under %f load' % get_load(root))

        # core
        sleep_cycle = poisson.get_sleep_cycle(root.lambd, data_threshold)
        logging.info('%s sleep cycle: %d' % (root.name, sleep_cycle))

        timeline = [[] for i in range(sleep_cycle)]
        timeline[0] = [i for i in root.target_device]
        timeline[0].append(root)
        timeline[0] = sorted(timeline[0], key=lambda d: d.name)
        return timeline

    except Exception as e:
        logging.exception(e)