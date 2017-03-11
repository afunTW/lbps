import sys
import logging

sys.path.append('../..')
import lbps.definition

# FIXME: keep buffer an bearer in type of list
class LBPSDevice(object):
    def __init__(self, name='device'):
        self.name = name
        self.buffer = {'backhaul': [], 'access': []}
        self.bearer = {'backhaul': [], 'access': []}
        self.sleep = False
        self.__interface = ''
        self.__transmission = ''

    @property
    def interface(self): return self.__interface
    @interface.setter
    def interface(self, interface):
        if isinstance(interface, str) and\
        interface in ['backhaul', 'access']:
            self.__interface = interface

    @property
    def transmission(self): return self.__transmission
    @transmission.setter
    def transmission(self, transmission):
        if isintance(transmission, str) and\
        transmission in ['downlink', 'uplink']:
            self.__transmission = transmission

    @property
    def lambd(self):
        # Bearer lambda aggregation
        flow_map = {
            'VoIP': traffic.VoIP(),
            'Video': traffic.Video(),
            'OnlineVideo': traffic.OnlineVideo()
        }

        aggr_bh = [flow_map[b.flow].lambd for b in self.bearer['backhaul']]
        aggr_ac = [flow_map[a.flow].lambd for a in self.bearer['access']]

        return {
            'backhaul': round(sum(aggr_bh), 2),
            'access': round(sum(aggr_ac), 2)
        }

    @property
    def wideband_capacity(self):
        if not self.__interface: return
        if not self.bearer[self.__interface]: return
        each_cqi = [bearer.CQI for bearer in self.bearer[self.__interface]]
        each_eff = [cqi.cqi_info(i)['eff'] for i in each_cqi]
        aggr_cap = sum([capacity.RE_TTI*eff for eff in each_eff])
        return aggr_cap