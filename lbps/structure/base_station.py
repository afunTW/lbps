import logging
import random
import sys

sys.path.append('../..')
from . import device
from src import bearer
from itertools import count


class BaseStation(device.OneHopDevice):
    count = count(0)

    def __init__(self, name=None):
        super(BaseStation, self).__init__()
        self.name = (
            name or '_'.join(
                [self.__class__.__name__, str(next(self.count))]
            )
        )

    def connect_to(self, dest, CQI, flow):
        assert (
            isinstance(dest, device.OneHopDevice) or
            isinstance(dest, device.TwoHopDevice)
            )

        self.append_bearer(bearer.Bearer(self, dest, CQI, flow))

        if isinstance(dest, device.OneHopDevice):
            dest.append_bearer(bearer.Bearer(dest, self, CQI, flow))
            logging.debug('Build direct bearer (%s, %s)' % (self.name, dest.name))
        elif isinstance(dest, device.TwoHopDevice):
            dest.backhaul.append_bearer(bearer.Bearer(dest, self, CQI, flow))
            logging.debug('Build backhaul bearer (%s, %s)' % (self.name, dest.name))
