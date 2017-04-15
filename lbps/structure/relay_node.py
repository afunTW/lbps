import sys
import logging

sys.path.append('../..')
from . import device
from . import base_station
from . import user_equipment
from src import bearer
from itertools import count


class RelayNode(device.TwoHopDevice):
    count = count(0)

    def __init__(self, name=None):
        self.name = (
            name or '_'.join(
                [self.__class__.__name__, str(next(self.count))]
            )
        )
        super(RelayNode, self).__init__(name=self.name)

    @property
    def lambd(self):
        return self.access.lambd

    def connect_to(self, dest, CQI, flow):
        assert isinstance(dest, device.OneHopDevice)

        if isinstance(dest, base_station.BaseStation):
            self.backhaul.append_bearer(bearer.Bearer(self, dest, CQI, flow))
            logging.debug('Build backhaul bearer (%s, %s)' % (self.name, dest.name))
        elif isinstance(dest, user_equipment.UserEquipment):
            self.access.append_bearer(bearer.Bearer(self, dest, CQI, flow))
            logging.debug('Build access bearer (%s, %s)' % (self.name, dest.name))

        dest.append_bearer(bearer.Bearer(dest, self, CQI, flow))
