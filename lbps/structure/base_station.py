from . import device
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
