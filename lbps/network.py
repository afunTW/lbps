# -*- coding: utf-8 -*-
#!/usr/bin/python3

from config import traffic

class Channel(object):
    def __init__(self, link='access', bandwidth=0, CQI=0):
        """
        property:
        [protected] link: identify the link is 'backhaul' or 'access'
        [protected] bandwidth: for calculating the capacity of the link (MHz)
        [protected] CQI: identify the channel quality of the link
        """
        self._link = link;
        self._bandwidth = bandwidth;
        self._CQI = CQI;

    @property
    def link(self):
        return self._link;
    @link.setter
    def link(self, link):
        try:
            if type(link) is str and (link.lower() is 'access' or link.lower() is 'backhaul'):
                self._link = link;
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

class Traffic(object):
    def __init__(self, flow):
        """
        given a traffic, related info will be assign
        this class can provide 'VoIP' and 'Video' so far
        """
        if flow in traffic:
            self._flow = flow;
            self._bitrate = traffic[flow].bitrate;
            self._pkt_size = traffic[flow].pkt_size;
            self._delay_budget = traffic[flow].delay_budget;
        else:
            print(str(flow) + " doesn't defined");

    @property
    def bitrate(self):
        return self._bitrate;

    @property
    def pkt_size(self):
        return self._pkt_size;

    @property
    def delay_budget(self):
        return self._delay_budget;
