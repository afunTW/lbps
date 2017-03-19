import sys
import random
import logging

sys.path.append('..')
from traffic import Traffic
from lbps.structure import device


class Bearer(object):
    def __init__(self, src, dest, CQI=0, flow=None):
        assert isinstance(src, device.OneHopDevice) and\
        isinstance(dest, device.OneHopDevice),\
        'connection device is not the lbps.structure.device instances'

        self.__source = src
        self.__destination = dest
        self.__CQI = CQI
        self.__flow = flow
        self.__CQI_type = {
            'L': [1,2,3,4,5,6],
            'M': [7,8,9],
            'H': [10,11,12,13,14,15]
        }

    @property
    def source(self):
        return self.__source

    @property
    def destination(self):
        return self.__destination

    @property
    def CQI(self):
        return self.__CQI

    @CQI.setter
    def CQI(self, value):
        if isinstance(value, str) and value in self.__CQI_type.keys():
            self.CQI = random.choice(self.__CQI_type[value])
        elif isinstance(value, list) and\
        set(value).issubset(list(self.__CQI_type.keys())):
            cqi_range = [self.__CQI_type[value] for t in value]
            cqi_range = [item for subset in _ for item in subset]
            self.__CQI = random.choice(cqi_range)
        elif isinstance(value, int) and value > 0 and value < 16:
            self.__CQI = value

    @property
    def flow(self):
        return self.__flow

    @flow.setter
    def flow(self, flow_type):
        try:
            assert isinstance(flow_type, Traffic),\
            'not the Traffic instance'
            self.__flow = flow_type
        except Exception as e:
            logging.exception(e)