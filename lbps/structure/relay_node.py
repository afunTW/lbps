from . import device
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
