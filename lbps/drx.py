import sys
import logging

from lbps.network_tools import LBPSWrapper
from lbps.structure.base_station import BaseStation
from lbps.structure.relay_node import RelayNode
from lbps.structure.user_equipment import UserEquipment
from itertools import count


class DRX(LBPSWrapper):
    count = count(0)
    def __init__(
        self,
        root,
        inactivity_timer,
        short_cycle_count,
        short_cycle_time,
        long_cycle_time,
        name=None
    ):
        self.name = (
            name or '_'.join(
                [self.__class__.__name__, str(next(self.count))]
            )
        )
        self.root = root
        self.inactivity_timer = inactivity_timer
        self.short_cycle_count = short_cycle_count
        self.short_cycle_time = short_cycle_time
        self.long_cycle_time = long_cycle_time
        self.demo_meta = None
        self.demo_summary = None
        self.__metadata = {}

        rn = self.root.target_device[0]
        self.__tdd_config = {
            'backhaul': rn.backhaul.tdd_config,
            'access': rn.access.tdd_config
        }

    def __metadata_update(self, metadata, src, record=True):
        # in drx mode: awake > no data > inactivity timer counting
        target = metadata[src]
        if target['inactivity_timer']:
            target['inactivity_timer'] -= 1
            if record: target['awake'] += 1
            src.sleep = False
        elif target['short_cycle_time']:
            target['short_cycle_time'] -= 1
            if record: target['sleep'] += 1
            src.sleep = True
        elif target['short_cycle_count']:
            target['short_cycle_count'] -= 1
            target['short_cycle_time'] = self.short_cycle_time
            if record: target['awake'] += 1
            src.sleep = False
        elif target['long_cycle_time']:
            target['long_cycle_time'] -= 1
            if record: target['sleep'] += 1
            src.sleep = True
        else:
            target['long_cycle_time'] = self.long_cycle_time
            if record: target['awake'] += 1
            src.sleep = False

    def __metadata_reset(self, metadata, src, record=True):
        src.sleep = False
        if record: metadata[src]['awake'] += 1
        metadata[src].update({
            'inactivity_timer': self.inactivity_timer,
            'short_cycle_count': self.short_cycle_count,
            'short_cycle_time': 0,
            'long_cycle_time': 0
        })

    def __transmit_packet(self, TTI, timeline, metadata=None, flush=False):

        def __transmit(pkt, src, dest, cap):
            dest.buffer.append(pkt)
            src.buffer.remove(pkt)
            return cap-pkt['size']

        record = True if not flush else False
        if not metadata:
            metadata = {
                d: {
                    'inactivity_timer': self.inactivity_timer,
                    'short_cycle_count': self.short_cycle_count,
                    'short_cycle_time': 0,
                    'long_cycle_time': 0,
                    'sleep': 0,
                    'awake': 0,
                    'delay': 0
                } for d in self.all_devices(self.root, RelayNode, UserEquipment)
            }

        # backhaul
        backhaul_activate_rn = []
        if self.__tdd_config['backhaul'][TTI%10] == 'D':

            # transmission
            available_cap = self.root.wideband_capacity
            for pkt in self.root.buffer:
                rn = pkt['device'].ref_access
                if available_cap < pkt['size']: break
                if flush or not rn.sleep:
                    backhaul_activate_rn.append(rn)
                    available_cap = __transmit(
                        pkt, self.root, rn.backhaul, available_cap)
            backhaul_activate_rn = list(set(backhaul_activate_rn))

            # metadata
            if not flush:
                for rn in backhaul_activate_rn:
                    self.__metadata_reset(metadata, rn, record=record)
                    for ue in rn.access.target_device:
                        self.__metadata_update(metadata, ue, record=record)

        # access
        for rn in self.root.target_device:
            transmit_direction = rn.access.tdd_config[TTI%10]
            if rn in backhaul_activate_rn or transmit_direction != 'D':
                continue

            if not rn.backhaul.buffer:
                self.__metadata_update(metadata, rn, record=record)
                for ue in rn.access.target_device:
                    self.__metadata_update(metadata, ue, record=record)
                continue

            self.__metadata_reset(metadata, rn, record=record)
            available_cap = rn.access.wideband_capacity
            activate_ue = []

            # transmission
            for pkt in rn.backhaul.buffer:
                ue = pkt['device']
                if available_cap < pkt['size']: break
                if flush or not ue.sleep:
                    activate_ue.append(ue)
                    available_cap = __transmit(
                        pkt, rn.backhaul, ue, available_cap)
                    metadata[ue]['delay'] += TTI - pkt['arrival_time']

            # metadata
            if not flush:
                for ue in rn.access.target_device:
                    if ue in activate_ue: self.__metadata_reset(metadata, ue, record=record)
                    else: self.__metadata_update(metadata, ue, record=record)

        return metadata

    def run(self, timeline):
        _time = self.root.simulation_time
        _all_src = self.all_devices(self.root, RelayNode, UserEquipment)
        _all_rn = self.all_devices(self.root, RelayNode)
        b_tdd = self.__tdd_config['backhaul']
        a_tdd = self.__tdd_config['access']
        is_downlink = lambda x: b_tdd[x%10] == 'D' or a_tdd[x%10] == 'D'
        metadata = {
            d: {
                'inactivity_timer': self.inactivity_timer,
                'short_cycle_count': self.short_cycle_count,
                'short_cycle_time': 0,
                'long_cycle_time': 0,
                'sleep': 0,
                'awake': 0,
                'delay': 0
            } for d in _all_src
        }

        logging.info('* Simulation begin with lambda {} Mbps = load {}'.format(
            self.root.lambd, self.root.load))
        self.clear_env(self.root)
        for d in _all_src: d.sleep = False

        # simulate packet arriving, TTI = 0 ~ simulation_time
        for TTI, pkt in timeline.items():
            if pkt: self.root.buffer += pkt
            if is_downlink(TTI):
                self.__transmit_packet(TTI, timeline, metadata)
            else:
                for d in _all_src: self.__metadata_update(metadata, d, record=True)

        # out of simulation time
        is_flush = lambda x, y: not x.buffer and all([not _.backhaul.buffer for _ in y])
        TTI = len(timeline)
        while not is_flush(self.root, _all_rn):
            if is_downlink(TTI):
                metadata = self.__transmit_packet(TTI, timeline, metadata, flush=True)
            else:
                for d in _all_src: self.__metadata_update(metadata, d, record=False)
            TTI += 1

        logging.info('* Simulation end with TTI {}'.format(TTI))
        self.demo_meta = metadata
        summary = self.summary_metadata(self.root, metadata)
        summary['lambda'] = self.root.lambd
        self.demo_summary = summary
        logging.info('summary = {}'.format(summary))
        return summary
