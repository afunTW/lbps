# -*- coding: utf-8 -*-
#!/usr/bin/python3

from config import traffic

class Channel(object):
    def __init__(self, interface='access', bandwidth=0, CQI=0, flow='VoIP'):
        """
        property:
        [protected] interface: identify the link is 'backhaul' or 'access'
        [protected] bandwidth: for calculating the capacity of the link (MHz)
        [protected] CQI: identify the channel quality of the link
        [protected] flow: flow type
        """
        self._interface = interface;
        self._bandwidth = bandwidth;
        self._CQI = CQI;

        if flow in traffic:
            self._flow = flow;
            self._bitrate = traffic[flow]['bitrate'];
            self._pkt_size = traffic[flow]['pkt_size'];
            self._delay_budget = traffic[flow]['delay_budget'];
        else:
            raise Exception(str(flow) + " doesn't defined");

    @property
    def interface(self):
        return self._interface;
    @interface.setter
    def interface(self, interface):
        try:
            if type(interface) is str and (interface.lower() is 'access' or interface.lower() is 'backhaul'):
                self._interface = interface;
            else:
                raise Exception("link should be str type and the value is 'access' or 'backhaul'")
        except Exception as e:
            print(e)

    @property
    def bandwidth(self):
        return self._bandwidth;
    @bandwidth.setter
    def bandwidth(self, bw):
        try:
            if type(bw) is int:
                self._bandwidth = bw;
            else:
                raise Exception("bandwidth should be the type of int (MHz)")
        except Exception as e:
            print(e);

    @property
    def CQI(self):
        return self._CQI;
    @CQI.setter
    def CQI(self, CQI):
        try:
            if type(CQI) is int:
                self._CQI = CQI;
            else:
                raise Exception("CQI should be the type of int")
        except Exception as e:
            print(e);

    @property
    def flow(self):
        return self._flow;

    @property
    def bitrate(self):
        return self._bitrate;

    @property
    def pkt_size(self):
        return self._pkt_size;

    @property
    def delay_budget(self):
        return self._delay_budget;
